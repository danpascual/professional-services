from google.cloud import storage
from google.oauth2.credentials import Credentials

from typing import Union

class FileOperations():
    """Class to interact with Google Cloud Storage"""

    def __init__(self, credentials: Union[Credentials, None], project: str, **kwargs):
        self._storage_client = storage.Client(credentials=credentials, project=project)

    def upload_file(self, bucket_name: str, blob_name: str, content: Union[str, bytes]):
        '''Uploads a file into a storage account bucket'''
        bucket = self._storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(data=content)

    def read_file(self, bucket_name: str, blob_name: str):
        '''Gets a storage account blob and reads it's content'''
        bucket = self._storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.download_as_bytes()