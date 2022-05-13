import os
import google.auth
from google.oauth2.credentials import Credentials
from shared_code.monitor_exception import MonitorException

class AuthService(object):
    """Handles Authentication to GCP"""

    @staticmethod
    def get_credentials() -> Credentials:
        try:
            credentials, project = google.auth.default()
            return credentials
        except Exception as ex:
            raise MonitorException(f"Authentication Error: {ex}")