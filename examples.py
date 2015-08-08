''' Quick test to check functionality on Gorgon '''
from gorgon import Gorgon

def operation_http(number):
    # Imports needs to be inside the function for cluster functionality
    import requests
    result = requests.get('http://localhost')
    # The result could be used to perform more operations, making complex
    # workflows
    return result.status_code


def operation_hash(number):
    # Imports needs to be inside the function for cluster functionality
    import hashlib
    # This is just an example of a computationally expensive task
    m = hashlib.sha512()
    for _ in range(4000):
        m.update('TEXT {}'.format(number).encode())
    digest = m.hexdigest()
    result = 'SUCCESS'
    if number % 5 == 0:
        result = 'FAIL'
    return result


def test():
    NUM_OPS=40000

    # Multiple goes can be used for ramping up
    test = Gorgon(operation_hash)
    test.go(num_operations=NUM_OPS, num_processes=1, num_threads=1)
    test.go(num_operations=NUM_OPS, num_processes=10, num_threads=10)
    test.go(num_operations=NUM_OPS, num_processes=20, num_threads=10)
    test.go(num_operations=NUM_OPS, num_processes=40, num_threads=50)
    print(test.small_report())
    print(test.html_graph_report())

    # HTTP testing is easy
    test = Gorgon(operation_http)
    test.go(num_operations=NUM_OPS, num_processes=1, num_threads=1)
    test.go(num_operations=NUM_OPS, num_processes=10, num_threads=10)
    test.go(num_operations=NUM_OPS, num_processes=20, num_threads=10)
    test.go(num_operations=NUM_OPS, num_processes=40, num_threads=50)
    print(test.small_report())
    print(test.html_graph_report())


    # Create a distributed test over a cluster defining your cluster
    SSH_KEY = '/path/to/key'
    test = Gorgon(operation_hash)
    test.add_to_cluster('node1', 'ssh_user', SSH_KEY)
    # You can configure the python interpreter to use on each box
    test.add_to_cluster('node2', 'ssh_user', SSH_KEY,
                        python_interpreter='/usr/bin/python3.4')
    # Run test as usual, now distributed over a cluster
    test.go(num_operations=NUM_OPS, num_processes=1, num_threads=1)
    test.go(num_operations=NUM_OPS, num_processes=10, num_threads=10)
    test.go(num_operations=NUM_OPS, num_processes=20, num_threads=10)
    test.go(num_operations=NUM_OPS, num_processes=40, num_threads=50)
    print(test.small_report())
    print(test.html_graph_report())


if __name__ == '__main__':
    test()
