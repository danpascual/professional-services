import requests
import json
import logging
from typing import Any

class Notifier:
    def __init__(self, url: str):
        self.url = url

    def post_alert(self, payload: Any):
        '''Post request'''
        if not self.url:
            logging.info('Notification url was not defined.')
            return None

        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(self.url, headers=headers, data=json.dumps(payload))
        if response.ok:
            logging.info('Post alert returned'.format(response.text))
        
        return response