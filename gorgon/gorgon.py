'''
Gorgon. A simple multiplier process analysis tool in Python
'''
from threading import Thread
from multiprocessing import Process, Queue
from copy import deepcopy
import sys
if sys.version > '3':
    from gorgon.report import GorgonReport
else:
    from report import GorgonReport
from uuid import uuid4
import inspect
from time import sleep
from random import randint
from collections import namedtuple
import imp

ClusterNode = namedtuple('ClusterNode', ('host', 'user', 'key'))

QUEUE = Queue()
RAND_DELAY_BASE = 0.001


def run_ops_thread(operation, seed, num_ops, report, delay):
    if delay:
        sleep(delay)

    for i in range(num_ops):
        number = seed + i
        call_id = str(uuid4())
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


TEMP_FILE_NAME = '/tmp/gorgon_file.py'


def run_cluster():
    # Read from the TEMP file
    # Get the parameters
    exec_file = sys.argv[1]
    fname = sys.argv[2]
    seed = int(sys.argv[3])
    num_ops = int(sys.argv[4])
    num_proc = int(sys.argv[5])
    num_threads = int(sys.argv[6])

    # Get the function from the temp file
    module = imp.load_source('operation', exec_file)
    operation = getattr(module, fname)

    # Initialize a Gorgon module and run the test
    harness = Gorgon(operation)
    harness.go(num_operations=num_ops, num_processes=num_proc,
               num_threads=num_threads, seed=seed, silent=True)
    print(harness.cluster_report())

class Gorgon(object):

    def __init__(self, operation):
        try:
            sig = inspect.signature(operation)
            if len(sig.parameters) != 1:
                raise Exception('A callable with one parameter '
                                'should be passed as operation')

        except TypeError:
            raise Exception('A callable should be passed as operation')
        except AttributeError:
            # This is Python2
            if not inspect.isfunction(operation):
                raise Exception('A callable should be passed as operation')
            if len(inspect.getargspec(operation).args) != 1:
                raise Exception('A callable with one parameter '
                                'should be passed as operation')


        self.operation = operation
        self.processes = []
        self.report = GorgonReport()
        # Store the source code of the call
        self._code = inspect.getsource(operation)
        self._code_name = operation.__name__
        self._cluster = None

    @property
    def num_nodes(self):
        if self._cluster is None:
            return None
        return len(self._cluster)

    def add_to_cluster(self, host, ssh_user, ssh_key_filename):
        try:
            import paramiko
        except ImportError:
            print('paramiko is needed for cluster support')
            raise

        node = ClusterNode(host=host, user=ssh_user,
                           key=ssh_key_filename)
        if not self._cluster:
            self._cluster = []

        self._cluster.append(node)

    def remove_from_cluster(self, host):
        '''
        Remove a node from the cluster. If called with 'all',
        removes all nodes
        '''
        if host == 'all':
            self._cluster = None

        # TODO: Remove from the _cluster array

    def start_pool(self):
        ''' Create a proper pool of workers '''

        for i in range(self.num_processes):
            args = (self.operation,
                    self.seed + (i * self.ops_per_process),
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
        cluster_factor = self.num_nodes if self._cluster else 1
        workers = self.num_threads * self.num_processes * cluster_factor
        if self.num_operations % workers != 0:
            close = (self.num_operations // workers) + 1
            suggestion = workers * close
            msg = 'Incorrect number of operations, maybe you mean {}?'
            raise Exception(msg.format(suggestion))

    def go(self, num_operations=1, num_processes=1, num_threads=1,
           seed=0, random_delay=False, silent=False):
        ''' Start the operations '''
        self.num_processes = num_processes
        self.num_threads = num_threads
        self.num_operations = num_operations
        self.seed = seed
        self.check_go()

        if self._cluster is not None:
            self.ops_per_node = num_operations // self.num_nodes
            self.start_cluster()
        else:
            # Start in non clustered way
            self.ops_per_process = num_operations // num_processes
            # Check the number matches
            self.random_delay = random_delay

            if not silent:
                self.print_report_header()

            self.start_pool()

            self.wait_until_finish()

    def start_cluster(self):
        import paramiko
        # Create the temp file and store the code
        tmp_file_name = TEMP_FILE_NAME
        with open(tmp_file_name, 'w') as fp:
            fp.write(self._code)

        # Send the code to all the clusters and start gorgon in cluster mode
        # there
        clients = []
        for node in self._cluster:
            # Connect to remote host
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(node.host, username=node.user,
                           key_filename=node.key)
            clients.append(client)

        for client in clients:
            # Setup sftp connection and transmit this script
            sftp = client.open_sftp()
            sftp.put(tmp_file_name, tmp_file_name)
            sftp.close()

        stdouts = []
        base_seed = self.seed
        for index, client in enumerate(clients):
            # Run the transmitted script remotely and show its output.
            # SSHClient.exec_command() returns the tuple (stdin,stdout,stderr)
            EXEC_TMPL = ('gorgon_cluster {exec_file} {fname} {seed} {num_ops} '
                         '{num_proc} {num_thread}'
                        )
            seed = base_seed + index * self.ops_per_node
            exec_command = EXEC_TMPL.format(exec_file=tmp_file_name,
                                            fname=self._code_name,
                                            seed=seed,
                                            num_ops=self.ops_per_node,
                                            num_proc=self.num_processes,
                                            num_thread=self.num_threads)

            stdin, stdout, stderr = client.exec_command(exec_command)
            stdouts.append(stdout)

        # Obtain the results through stdout
        for stdout in stdouts:
            for line in stdout:
                self.report.append_cluster(line)

        # cleanup
        for client in clients:
            client.exec_command('rm {}*'.format(tmp_file_name))
            client.close()

    def small_report(self):
        return self.report.small_report()

    def html_graph_report(self):
        return self.report.html_graph_report()

    def cluster_report(self):
        return self.report.cluster_report()

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
        call_id = str(uuid4())
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
