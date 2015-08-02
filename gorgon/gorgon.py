'''
Gorgon. A performant loadtest tool Python
'''
from threading import Thread
from multiprocessing import Process, Queue
from copy import deepcopy
from report import GorgonReport
from uuid import uuid4
import inspect

QUEUE = Queue()


def run_ops_thread(operation, seed, num_ops, report):
    for i in range(num_ops):
        number = seed + i
        report.start_call(number)
        try:
            result = operation(number)
        except Exception as exc:
            result = str(exc)

        report.end_call(number, result)


def start_process(operation, seed, num_ops, num_threads):
    report = GorgonReport()
    num_ops_thread = num_ops // num_threads
    threads = []
    for i in range(num_threads):
        thread_seed = seed + i * num_ops_thread
        args = (operation, thread_seed, num_ops_thread, report)
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

    def start_pool(self):
        ''' Create a proper pool of workers '''

        for i in range(self.num_processes):
            args = (self.operation,
                    i * self.ops_per_process,
                    self.ops_per_process,
                    self.num_threads)
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


    def go(self, num_operations=None, num_processes=1, num_threads=1):
        ''' Start the operations '''
        # TODO: Check the number matches
        # self.check_numbers()
        self.num_processes = num_processes
        self.num_threads = num_threads
        self.ops_per_process = num_operations // num_processes

        self.report = GorgonReport()
        self.start_pool()

        self.wait_until_finish()
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
        # result = 200
        self.report.end_call(call_id)
        result.previous_url = url
        result.previous_method = method
        return result
