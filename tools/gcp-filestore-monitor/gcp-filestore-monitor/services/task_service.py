from google.oauth2.credentials import Credentials
from google.cloud import tasks_v2 as tasks
from shared_code.utilities import Utilities

import json
import hashlib

class TaskService(object):

    def __init__(self, queue: str, service_account: str, endpoint: str, credentials: Credentials = None):
        self.client = tasks.CloudTasksAsyncClient(credentials=credentials)
        
        self.endpoint = endpoint
        self.parent = queue
        self.service_account = service_account

    async def create_task(self, task_name: str, data: list[dict]):
           
        task = {
            "http_request": {
                "http_method": tasks.HttpMethod.POST,
                "url": self.endpoint,
                "oidc_token": {
                    "service_account_email": self.service_account,
                    "audience": self.endpoint
                },
                "headers": { "Content-type": "application/json" }
            }
        }

        if data is not None:
            # convert to json and convert it to bytes
            payload = json.dumps(data).encode()

            task["http_request"]["headers"] = { "Content-type": "application/json" }
            task["http_request"]["body"] = payload

        if task_name is not None:
            # Add the name to tasks.
            task["name"] = task_name

        response = await self.client.create_task(request={ "parent": self.parent, "task": task })
        return response

    @staticmethod
    def create_task_name(project: str, location: str, queue_name: str, task_name: str):
        name = hashlib.sha256(task_name.encode()).hexdigest()
        return tasks.CloudTasksAsyncClient.task_path(project, location, queue_name, name)

    @staticmethod
    def parse_queue_path(queue_name: str) -> dict:
        return tasks.CloudTasksAsyncClient.parse_queue_path(queue_name)