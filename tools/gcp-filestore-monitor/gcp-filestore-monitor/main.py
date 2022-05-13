import functions_framework
from flask import Request, Response, abort
from typing import Union
from google.oauth2.credentials import Credentials
from google.api_core.exceptions import PermissionDenied
from prometheus_client import generate_latest, CollectorRegistry
from shared_code.configuration import Configuration
from shared_code.file_operations import FileOperations
from shared_code.monitor_exception import MonitorException
from shared_code.utilities import Utilities
from shared_code.metadata_service import MetadataService
from shared_code.publisher import Publisher
from notifications.resize_subscriber import ResizeSubscriber
from services.auth_service import AuthService
from services.project_service import ProjectService
from services.filestore_service import FilestoreService
from services.monitor_service import MonitorService
from filestore_collector import FilestoreCollector

import os
import logging
import asyncio
import traceback
import itertools
import warnings
warnings.filterwarnings("ignore")

@functions_framework.http
def filestore_monitor(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
    logging.basicConfig(level=LOGLEVEL)
    result = b''
    try:
        host_project = MetadataService.get_current_project()
        logging.info(f"Current Project: {host_project}")
        bucket_name = os.environ['BUCKET_NAME']
        blob_name = os.environ['BLOB_NAME']
        credentials = AuthService.get_credentials()
        
        fo = FileOperations(credentials, host_project)
        if request.method == "GET":
            logging.info("Fetching information from file")
            result = fo.read_file(bucket_name, blob_name)

        elif request.method == "POST":
            logging.info("Regenerating results")
            result = asyncio.run(__process(request, credentials))
            if result:
                fo.upload_file(bucket_name, blob_name, result)
        else:
            abort(405)
    except Exception as ex:
        logging.error(f"An error occurred: {ex}")
        logging.debug(traceback.format_exc())
        return abort(500)
    
    return Response(result, mimetype="text/plain")
    

async def __process(request: Request, credentials: Credentials):
    """Begins asynchronic process"""

    logging.info("Fetching request information")
    monitor_period = 300
    if request.is_json:
        monitor_period = request.json["monitor_period"]
    logging.info(f"Metrics period: {monitor_period}")
    logging.info("Fetching configuration")
    config = Configuration.get_configuration()
    tiers = config["tiers"]
    # Allow for resizing the Enterprise tier capacity limit through Environment Variables
    if int(os.environ.get("RESIZE_ENTERPRISE_MAX_CAPACITY", 0)) > 0: 
        Configuration.adjust_tier_max_capacity(tiers, "ENTERPRISE", os.environ.get("RESIZE_ENTERPRISE_MAX_CAPACITY", 0))
    
    pub = __register_notification_subscribers(credentials=credentials)

    logging.info("Fetching projects")
    project_client = ProjectService(credentials=credentials)
    projects= await project_client.get_projects()
    logging.info("Fetching metrics")
    metrics = await __get_metrics(projects, tiers, metric_interval=monitor_period, credentials=credentials)
    
    if metrics:
        # Register Notification Subscribers
        await pub.dispatch(metrics)

    logging.info("Call Prometheus collector")
    result = __collector(metrics) 
    return result


async def __get_metrics(projects: list[str], tiers: list, metric_interval: int = 3600, number_threads: int = 10, credentials: Credentials = None) -> list[dict]:
    '''Handles the metric retrieval for multiple projects'''
    
    #Define clients
    asset_client = FilestoreService(credentials=credentials)
    monitor_client = MonitorService(interval=metric_interval, credentials=credentials)
    
    tasks = [asyncio.create_task(__get_metric(asset_client, monitor_client, project, tiers)) for project in projects]
    results = (await Utilities.gather_with_concurrency(number_threads, *tasks))

    return list(itertools.chain(*results))


async def __get_metric(asset_client: FilestoreService, monitor_client: MonitorService, project, tiers: list) -> list[dict]:
    """Get all the metrics for a single Instance"""

    try:
        logging.info(f"Gathering metrics for project: {project}")
        assets = await asset_client.get_filestore_assets(project)
        if not assets:
            return []

        __calculate_limits(assets, tiers)
        await monitor_client.calculate_usage_metrics(assets, project)

        return assets
    except PermissionDenied:
        logging.warn(f"Permission denied for project: {project}")
    except Exception as ex:
        logging.error(f"Unexpected error on project {project}: {ex}")
        logging.debug(traceback.format_exc())
    return []

def __calculate_limits(assets: list[dict], tiers: list[dict]):
    """Calculates the Filestore IOPS and TPUT limits based on it's capacity."""
    for asset in assets:
        tier = next(tier for tier in tiers if asset["tier"] in tier["name"])
        performance = tier["performance"]
        
        if tier is None or performance is None: continue

        asset["allow_resize"] = bool(tier.get("allow_resize", False))
        asset["MAX_CAPACITY"] = tier.get("max_capacity_gb", 0)
        
        if performance["scale_type"] == "FIXED":
            limit= next(scale for scale in performance["scaling"] if asset["capacity"] <= scale["limit_gb"])
            if limit is None:
                continue
            asset["MAX_READ_IOPS"] = limit["read_iops"]
            asset["MAX_WRITE_IOPS"] = limit["write_ips"]
            asset["MAX_READ_THROUGHPUT"] = limit["read_tp_mbps"]
            asset["MAX_WRITE_THROUGHPUT"] = limit["write_tp_mbps"]
        elif performance["scale_type"] == "LINEAR":
            capacity = asset["capacity"]
            # We still get the 1TB like performance for capacities below 1TB
            if performance["min_performance_gb"] and capacity < int(performance["min_performance_gb"]):
                capacity = int(performance["min_performance_gb"])

            steps = capacity / performance["step_gb"]
            asset["MAX_READ_IOPS"] = steps * performance["scaling"]["read_iops"]
            asset["MAX_WRITE_IOPS"] = steps * performance["scaling"]["write_iops"]
            asset["MAX_READ_THROUGHPUT"] = steps * performance["scaling"]["read_tp_mbps"]
            asset["MAX_WRITE_THROUGHPUT"] = steps * performance["scaling"]["write_tp_mbps"]


def __register_notification_subscribers(credentials: Credentials = None) -> Publisher:
    # Register Notification Subscribers
    publisher = Publisher()
    
    if (os.environ.get("RESIZE_ENABLED", "0") == "1"):
        publisher.register(ResizeSubscriber(credentials))

    return publisher

def __collector(metrics: list[dict]) -> bytes:
    '''Parses the results to prometheus format'''
    registry=CollectorRegistry()
    fsCollector = FilestoreCollector(metrics)
    registry.register(fsCollector)
    result = generate_latest(registry=registry)
    registry.unregister(fsCollector)
    return result