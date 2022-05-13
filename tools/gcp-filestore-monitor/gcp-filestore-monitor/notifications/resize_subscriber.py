from google.oauth2.credentials import Credentials
from services.task_service import TaskService
from shared_code.utilities import Utilities
from google.api_core.exceptions import AlreadyExists

import os
import traceback
import logging

class ResizeSubscriber:
    def __init__(self, credentials: Credentials = None):
        self.credentials = credentials

        self.threshold = float(os.environ.get("RESIZE_USAGE_THRESHOLD", 0))
        self.queue = os.environ.get("RESIZE_QUEUE_NAME", "")
        self.service_account = os.environ.get("RESIZE_QUEUE_SA", "")
        self.endpoint = os.environ.get("RESIZE_ENDPOINT", "")
        self.increase_percentage = int(os.environ.get("RESIZE_INCREASE_PERCENTAGE", 10))

    async def send(self, payload):
        '''Send message to resize process'''
        resize_items = [{"name": item["instance_name"], 
                        "capacity": item["capacity"], 
                        "increase_percentage": self.increase_percentage} 
            for item in payload if item["allow_resize"]
                and item["USED_PERCENTAGE"] != 0 
                and item["USED_PERCENTAGE"] >= self.threshold
                and (item["MAX_CAPACITY"] == 0 or item["capacity"] < item["MAX_CAPACITY"])
        ]
        
        if not resize_items: return

        if (os.environ.get("LOCAL", "") == "1") and not self.queue:
            #TODO If local environment, call resize process directly
            await Utilities.post_message(self.endpoint, resize_items)
            logging.info("Request submitted.")
        else:
            if not self.queue:
                logging.warn("No queue was provided")
                return
            
            client = TaskService(self.queue, self.service_account, self.endpoint, self.credentials)
            
            for metrics_chunk in Utilities.chunks(resize_items, 20):
                if not metrics_chunk: continue
                try:
                    task_response = await client.create_task(None, metrics_chunk)
                    logging.info(f"Created task {task_response.name}")
                except AlreadyExists as ex:
                    logging.error(f"An error occurred: {ex}")
                except Exception as ex:
                    logging.error(f"An error occurred: {ex}")
                    logging.debug(traceback.format_exc())
                
