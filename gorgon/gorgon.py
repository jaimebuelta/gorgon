'''
Gorgon. A performant loadtest tool Python
'''
from threading import Thread
from multiprocessing import Process, Queue
from copy import deepcopy
from report import GorgonReport
from uuid import uuid4
import inspect
from time import sleep
from random import randint

QUEUE = Queue()
RAND_DELAY_BASE = 0.001


def run_ops_thread(operation, seed, num_ops, report, delay):
    if delay:
        sleep(delay)

    for i in range(num_ops):
        number = seed + i
        call_id = uuid4()
        report.start_call(call_id)
        try:
            result = operation(number)
        except Exception as exc:
            result = exc

        report.end_call(call_id, str(result))


def start_process(operation, seed, num_ops, num_threads, random_delay):
    report = GorgonReport()
    num_ops_thread = num_ops // num_threads
    threads = []
    delay = 0
    for i in range(num_threads):
        thread_seed = seed + i * num_ops_thread
        if random_delay:
            delay = randint(0, num_threads) * RAND_DELAY_BASE
        args = (operation, thread_seed, num_ops_thread, report,
                delay)
        thread = Thread(target=run_ops_thread, args=args)
        thread.start()
        threads.append(thread)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    QUEUE.put(report)

    return report


class Gorgon(object):

    def __init__(self, operation):
        try:
            sig = inspect.signature(operation)
            if len(sig.parameters) != 1:
                raise Exception('A callable with one parameter '
                                'should be passed as operation')

        except TypeError:
            raise Exception('A callable should be passed as operation')

        self.operation = operation
        self.processes = []
        self.report = GorgonReport()

    def start_pool(self):
        ''' Create a proper pool of workers '''

        for i in range(self.num_processes):
            args = (self.operation,
                    i * self.ops_per_process,
                    self.ops_per_process,
                    self.num_threads,
                    self.random_delay)
            process = Process(target=start_process,
                            args=args)
            process.start()
            self.processes.append(process)


    def insert(self, priority, profile):
        self.queue.put((priority, deepcopy(profile)))

    def wait_until_finish(self):
        # This sometimes fail
        # for process in self.processes:
        #     process.join()

        num_reports = 0
        # Get all the reports on the queue
        while num_reports < self.num_processes:
            report = QUEUE.get()
            self.report.append(report)
            num_reports += 1

    def check_go(self):
        '''
        Check that the number of operations, processes and
        threads adds up
        '''
        workers = self.num_threads * self.num_processes
        if self.num_operations % workers != 0:
            close = (self.num_operations // workers) + 1
            suggestion = workers * close
            msg = 'Incorrect number of operations, maybe you mean {}?'
            raise Exception(msg.format(suggestion))

    def go(self, num_operations=1, num_processes=1, num_threads=1,
           random_delay=False, silent=False):
        ''' Start the operations '''
        self.num_processes = num_processes
        self.num_threads = num_threads
        self.num_operations = num_operations
        self.check_go()
        self.ops_per_process = num_operations // num_processes
        # Check the number matches
        self.random_delay = random_delay

        if not silent:
            self.print_report_header()

        self.start_pool()

        self.wait_until_finish()

    def print_report(self):
        self.report.print_report()

    def html_report(self):
        self.report.html_report()

    def print_report_header(self):
        TMPL = 'Run operation {} times, with {} processes * {} threads'
        msg = TMPL.format(self.num_operations,
                          self.num_processes,
                          self.num_threads)
        print(msg)

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
        # result = 200
        self.report.end_call(call_id)
        result.previous_url = url
        result.previous_method = method
        return result
