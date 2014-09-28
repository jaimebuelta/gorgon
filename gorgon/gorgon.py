'''
Gorgon. A performant loadtest tool Python
'''
from multiprocessing import Process, JoinableQueue
import requests


def worker(queue):

    while True:
        new_call = queue.get()
        print('call {}'.format(new_call))
        callback = new_call.pop('callback', None)
        result = Gorgon.http_call(new_call)
        queue.task_done()

        # Enter in the queue a possible callback
        if callback:
            new_profile = callback(result)
            if new_profile:
                queue.put(new_profile)


class Gorgon(object):

    MAP_METHODS = {
        'GET': requests.get,
        'OPTIONS': requests.options,
        'HEAD': requests.head,
        'POST': requests.post,
        'PUT': requests.put,
        'PATCH': requests.patch,
        'DELETE': requests.delete,
    }

    def __init__(self, profiles):
        if not profiles:
            raise Exception('Please define some profile')

        if getattr(profiles, 'items', None) is None:
            raise Exception('Profiles needs to be a dictionary')

        self.profiles = profiles

        # TODO: Set up the number of workers
        self.num_workers = 4
        self.queue = JoinableQueue()

    def start_pool(self):
        ''' Create a proper pool of workers '''

        for _ in range(self.num_workers):
            p = Process(target=worker, args=(self.queue,))
            p.daemon = True
            p.start()

    def insert(self, profile):
        self.queue.put(profile)

    def go(self, num_requests=None, time=None):
        ''' Start the tests defined on profiles '''

        # Create the initial queue of profiles
        for weight, profile in self.profiles.items():
            for _ in range(weight * num_requests):
                self.insert(profile)

        self.start_pool()
        self.queue.join()

    @classmethod
    def http_call(cls, params):
        '''
        This function abstracts the access to http calls
        '''
        # TODO: If url is not present, log an error
        url = params.pop('url')
        method = params.pop('method')
        requests_function = cls.MAP_METHODS[method]
        result = requests_function(url, **params)
        result.previous_url = url
        result.previous_method = method
        return result
