''' Quick test to check functionality on Gorgon '''
from gorgon import Gorgon
import requests
import hashlib

def operation_http(number):
    result = requests.get('http://localhost')
    return result.status_code


def operation_hash(number):
    m = hashlib.sha512()
    for _ in range(400):
        m.update('TEXT {}'.format(number).encode())
    digest = m.hexdigest()
    return 'SUCCESS'


def test():
    NUM_OPS=4000
    # for i in range(NUM_OPS):
    #     operation(i)

    test = Gorgon(operation_hash)
    test.go(num_operations=NUM_OPS, num_processes=1, num_threads=1)
    # test.print_report()
    test.go(num_operations=NUM_OPS, num_processes=10, num_threads=10)
    # test.print_report()
    test.go(num_operations=NUM_OPS, num_processes=20, num_threads=10)
    # test.print_report()
    test.go(num_operations=NUM_OPS, num_processes=40, num_threads=50)
    print(test.html_report())

if __name__ == '__main__':
    test()
