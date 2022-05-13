import typing
from google.oauth2.credentials import Credentials
from google.cloud import monitoring_v3 as monitoring
from google.cloud.monitoring_v3.services.metric_service import pagers

import time
import logging

class MonitorService(object):
    """Handles operations related to the GCP Monitor Service"""
        
    def __init__(self, interval: int = 3600, credentials: Credentials = None):
        self.client = monitoring.MetricServiceAsyncClient(credentials=credentials)
        self.interval = interval
        self.aggregation_period = interval

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value: int):
        if value is None:
            raise ValueError("The interval must be numeric")

        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10 ** 9)
        self._interval = monitoring.TimeInterval({
            "end_time": { "seconds": seconds, "nanos": nanos },
            "start_time": { "seconds": (seconds - value), "nanos": nanos }
        })

    @property
    def aggregation_period(self):
        return self._aggregation_period
    
    @aggregation_period.setter
    def aggregation_period(self, value: int):
        if value is None:
            raise ValueError("The aggregation period must be numeric")
        self._aggregation_period = value

    async def calculate_usage_metrics(self, assets: list[dict], project: str):
        '''Handles the metric retrieval for a single project and maps the results'''

        request={
            "name": f"projects/{project}",
            "filter": 'metric.type = "file.googleapis.com/nfs/server/used_bytes_percent"',
            "interval": self.interval,
            "view": monitoring.ListTimeSeriesRequest.TimeSeriesView.FULL,
            "aggregation": monitoring.Aggregation({
                "alignment_period": { "seconds": self.aggregation_period },
                "per_series_aligner": monitoring.Aggregation.Aligner.ALIGN_MEAN
            })
        }

        try:
            def calc_percentage(asset: dict, value: float):
                asset["USED_PERCENTAGE"] = round(value, 2)
            
            metrics = await self.client.list_time_series(request)
            #await self.__parse_usage_metrics(assets, metrics)
            await MonitorService.__generic_parser(assets, metrics, calc_percentage)
        except Exception as ex:
            logging.error(f"An error occurred while fetching the usage: {ex}")
            
    
    @staticmethod
    async def __generic_parser(assets: typing.List[dict], 
                                metrics: pagers.ListTimeSeriesAsyncPager, 
                                calc_percentage: typing.Callable[[typing.Any, float], None]):
        """Fills asset with metrics value"""
        async for metric in metrics:
            project = metric.resource.labels["project_id"]
            location = metric.resource.labels["location"]
            instance_name = metric.resource.labels["instance_name"]
            
            asset= next((fs for fs in assets if fs["instance_name"] == f"projects/{project}/locations/{location}/instances/{instance_name}"), None)
            if (not asset):
                #logging.error(f"{metric_type} Metric for filestore {instance_name} not found")
                continue
            
            metric_value = metric.points[0].value.double_value if metric.points else 0
            calc_percentage(asset, metric_value)