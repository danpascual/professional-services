from google.oauth2.credentials import Credentials
from google.cloud import resourcemanager_v3 as resourcemanager

from shared_code.monitor_exception import MonitorException

import os
import re
import logging
import traceback

class ProjectService(object):
    """Handles operations related to GCP Projects"""

    def __init__(self, credentials: Credentials = None):
        self.client = resourcemanager.ProjectsAsyncClient(credentials=credentials)
        self.pattern = os.environ["PROJECT_PATTERN"]

    async def get_projects(self) -> list[str]:
        """Retrieves a list of projects"""
        try:
            # Only for testing read the list of projects from environment variables.
            project_ids = os.environ.get("PROJECT_ID", "")
            if (os.environ.get("LOCAL", "") == "1" or project_ids):
                #if project_ids:
                return project_ids.split(',')
                
            scope = os.environ["SCOPE"]
            projects = await self.client.list_projects(parent=scope)
            # Only return projects with specific format
            result= [p.project_id async for p in projects if re.search(self.pattern, p.project_id)]
            return result
        except Exception as ex:
            logging.error(traceback.format_exc())
            raise MonitorException(f"Error retrieving the list of projects: {ex}")