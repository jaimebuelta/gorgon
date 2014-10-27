'''
Gorgon. A performant loadtest tool Python
'''
from threading import Thread
from queue import PriorityQueue
from random import randint, random
from copy import deepcopy
import requests
from report import GorgonReport
from uuid import uuid4


NUM_WORKERS = 4
MIN_PRIO_ADJ_VALUE = NUM_WORKERS / 2
MAX_PRIO_ADJ_VALUE = NUM_WORKERS + MIN_PRIO_ADJ_VALUE


def prio_adjusted():
    return randint(MIN_PRIO_ADJ_VALUE, MAX_PRIO_ADJ_VALUE) + random()


def worker(gorgon):

    while True:
        prio, new_call = gorgon.queue.get()
        callback = new_call.pop('callback', None)
        result = gorgon.http_call(new_call)
        gorgon.queue.task_done()

        # Enter in the queue a possible callback
        if callback:
            new_profile = callback(result)
            if new_profile:
                try:
                    new_prio = prio + prio_adjusted()
                    item = new_prio, deepcopy(new_profile)
                    gorgon.queue.put(item)
                except TypeError:
                    new_prio = prio + prio_adjusted()
                    item = new_prio, deepcopy(new_profile)
                    gorgon.queue.put(item)


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
        self.num_workers = NUM_WORKERS
        self.queue = PriorityQueue()

    def start_pool(self):
        ''' Create a proper pool of workers '''

        for _ in range(self.num_workers):
            p = Thread(target=worker, args=(self,))
            p.daemon = True
            p.start()

    def insert(self, priority, profile):
        self.queue.put((priority, deepcopy(profile)))

    def go(self, num_requests=None, time_limit=None):
        ''' Start the tests defined on profiles '''

        # Create the initial queue of profiles
        for weight, profile in self.profiles.items():
            for prio in range(weight * num_requests):
                self.insert(prio, profile)

        self.report = GorgonReport()
        self.start_pool()
        self.queue.join()
        self.report.end()
        self.report.print_report()

    def http_call(self, params):
        '''
        This function abstracts the access to http calls
        '''
        call_id = uuid4()
        # TODO: If url is not present, log an error
        url = params.pop('url')
        method = params.pop('method')
        requests_function = self.MAP_METHODS[method]
        self.report.start_call(call_id, url)
        result = requests_function(url, **params)
        self.report.end_call(call_id)
        result.previous_url = url
        result.previous_method = method
        return result
