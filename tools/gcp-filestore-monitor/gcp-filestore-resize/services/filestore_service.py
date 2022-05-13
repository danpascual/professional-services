from google.oauth2.credentials import Credentials
from google.cloud import filestore_v1 as filestore
from google.cloud.filestore_v1.types import Instance, FileShareConfig
from google.protobuf.field_mask_pb2 import FieldMask
from shared.invalid_exception import CapacityMissmatchException

import math
import logging
import asyncio

class FilestoreService(object):

    def __init__(self, credentials: Credentials):
        self.client = filestore.CloudFilestoreManagerAsyncClient(credentials=credentials)
        self.update_mask = FieldMask()
        self.update_mask.FromJsonString("fileShares")

    async def get_filestore(self, instance_name: str) -> Instance:
        '''Retrieves the data of a filestore instance'''
        return await self.client.get_instance(name=instance_name)


    async def update_filestore(self, instance: Instance):
        '''Updates the filestore instance'''
        update_request = filestore.UpdateInstanceRequest(instance=instance, update_mask=self.update_mask)
        await self.client.update_instance(update_request)
        # update doesnt happen instantly, so giving the gcp time to update the filestore

    @staticmethod
    def calculate_capacity(instance: Instance, current_capacity_gb: int, increase_percentage: float, increment_step_gb: int) -> bool:
        '''Calculates the new capacity for the instance'''
        # Get the only volume in the instance (might need to add filter)
        share: FileShareConfig = next(share for share in instance.file_shares)
        if share is None:
            return False

        # Capacity missmatch validation
        if share.capacity_gb != current_capacity_gb:
            raise CapacityMissmatchException("Provided capacity doesnt match the current state of the instance")

        new_capacity = share.capacity_gb * (1 + increase_percentage)
        new_capacity = int(math.ceil(new_capacity / increment_step_gb) * increment_step_gb)
        logging.info(f"Instance: {instance.name}, Volume: {share.name}, Tier: {instance.tier}, Original Capacity: {share.capacity_gb}, New Capacity: {new_capacity}")
        share.capacity_gb = new_capacity
        return True