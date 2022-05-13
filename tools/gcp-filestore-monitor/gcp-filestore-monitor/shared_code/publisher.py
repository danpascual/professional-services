import asyncio

class Publisher(list):
    def __init__(self):
        self.subscribers = dict()

    def register(self, subscriber, callback=None):
        '''Register subscribers that will be notified'''
        if callback is None:
            callback = getattr(subscriber, 'send')
        self.subscribers[subscriber] = callback

    def unregister(self, subscriber):
        '''Unregister subscribers to stop being notified'''
        del self.subscribers[subscriber]

    async def dispatch(self, payload):
        '''Send notifications to all registered subscribers'''
        tasks = []
        for subscriber, callback in self.subscribers.items():
            tasks.append(asyncio.create_task(callback(payload)))
        
        await asyncio.gather(*tasks)