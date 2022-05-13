import re
import typing
import functions_framework
from flask import Request, Response, abort
from google.auth import credentials
from services.auth_service import AuthService
from services.filestore_service import FilestoreService
from shared.configuration import Configuration
from shared.utilities import Utilities
from shared.invalid_exception import InvalidRequestException

import os
import traceback
import asyncio
import logging
import warnings
warnings.filterwarnings("ignore")



@functions_framework.http
def filestore_resize(request: Request):
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

    try:
        if request.method == "POST":
            asyncio.run(__process(request))
        else:
            abort(405)
    except InvalidRequestException as ex:
        return abort(400)
    except Exception as ex:
        logging.error(f"An error occurred. {ex}")
        logging.error(traceback.format_exc())
        return abort(500)

    return Response("Completed", mimetype="text/plain")


async def __process(request: Request, number_threads: int = 20):
    """Begins asynchronic process"""
    
    logging.info("Fetching configuration")
    config = Configuration.get_configuration()
    tiers = config["tiers"]
    #Define clients
    credentials = AuthService.get_credentials()
    client = FilestoreService(credentials=credentials)

    update_items = request.json
    if not update_items:
        raise InvalidRequestException("No instances provided.")

    tasks = [asyncio.create_task(__update_instance(client, item, tiers)) for item in update_items]
    await Utilities.gather_with_concurrency(number_threads, *tasks)
    await asyncio.sleep(10)


async def __update_instance(client: FilestoreService, item: dict, tiers: list):
    """Fetches the provided filestore instance from GCP, calculates the new capacity and send the update request to GCP"""
    try:
        # Retrieve the current instance
        instance = await client.get_filestore(item["name"])
        if instance is None:
            logging.error(f"instance: {item['name']} not found.")
            return

        # Get the instance Tier from configuration
        tier = next((tier for tier in tiers if instance.tier in tier["name"]), None)
        if tier is None:
            logging.error(f"Tier for instance: {item['name']} not found.")
            return

        increase_percentage = int(item.get("increase_percentage", 10)) * 0.01
        # Calculate new capacity and update instance
        if (FilestoreService.calculate_capacity(instance, item['capacity'], increase_percentage, int(tier["increments_gb"]))):
            await client.update_filestore(instance)
            logging.info(f"Instance updated: {instance.name}")
        else:
            logging.error(f"Unable to update capacity for instance: {instance.name}")
    except Exception as ex:
        logging.error(f"An error occurred. {ex}")