from typing import Any

import json
import asyncio
import requests
import logging

class Utilities(object):

    @staticmethod
    def chunks(lst: list, n: int):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    @staticmethod
    async def gather_with_concurrency(n: int, *tasks):
        """Limits tasks concurrency to n sized chunks"""
        semaphore = asyncio.Semaphore(n)

        async def sem_task(task):
            async with semaphore:
                return await task
        return await asyncio.gather(*(sem_task(task) for task in tasks))

    @staticmethod
    async def post_message(url: str, payload: Any):
        '''Post request'''
        if not url:
            logging.info('Notification url was not defined.')
            return None

        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        logging.info('Post alert returned'.format(response.text))
        return response