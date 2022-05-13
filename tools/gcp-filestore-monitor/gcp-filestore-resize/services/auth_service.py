import os
import google.auth
from google.oauth2.credentials import Credentials

class AuthService(object):

    @staticmethod
    def get_credentials() -> Credentials:
        credentials, project = google.auth.default()
        return credentials