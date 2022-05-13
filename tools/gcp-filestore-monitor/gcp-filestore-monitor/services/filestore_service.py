from google.oauth2.credentials import Credentials
from google.cloud import filestore_v1 as filestore
from google.cloud.filestore_v1.types import Instance

import re

class FilestoreService(object):
    """Handles operations related to GCP Filestore Services"""

    def __init__(self, credentials: Credentials = None):
        self.client = filestore.CloudFilestoreManagerAsyncClient(credentials=credentials)
        

    async def get_filestore_assets(self, project_id: str) -> list[dict]:
        
        instances = await self.client.list_instances(parent=f"projects/{project_id}/locations/-")
        
        result=[]
        instance: Instance
        async for instance in instances: #type: Instance
            #volume: FileShareConfig
            short_name = instance.name.rsplit('/', 1)[-1]
            for volume in instance.file_shares:
                id = f"{instance.name}/{volume.name}".lower()
                result.append({
                    "id": id,
                    "project": project_id,
                    "location": FilestoreService.find_location(instance.name),
                    "instance_name": instance.name,
                    "instance_sname": short_name, 
                    "vol_name": volume.name,
                    "type": "file.googleapis.com/Instance",
                    "capacity": int(volume.capacity_gb),
                    "tier": int(instance.tier),
                    "allow_resize": False,
                    "MAX_CAPACITY": 0,
                    "MAX_READ_IOPS": 0,
                    "MAX_WRITE_IOPS": 0,
                    "MAX_READ_THROUGHPUT": 0,
                    "MAX_WRITE_THROUGHPUT": 0,
                    "USED_PERCENTAGE": 0,
                    "READ_OPS_PERCENTAGE": 0,
                    "WRITE_OPS_PERCENTAGE": 0,
                    "READ_TPUT_PERCENTAGE": 0,
                    "WRITE_TPUT_PERCENTAGE": 0
                })

        return result

    @staticmethod
    def find_location(instance_name: str) -> str:
        matches = re.search('.*/locations/(.*)/instances/.*', instance_name)
        if matches:
            return matches.group(1)
        return None