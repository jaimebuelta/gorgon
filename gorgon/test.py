''' Quick test to check functionality on Gorgon '''
from gorgon import Gorgon
import requests
import hashlib

def operation_http(number):
    result = requests.get('http://localhost')
    return result.status_code


def operation_hash(number):
    m = hashlib.sha512()
    for _ in range(4000):
        m.update('TEXT {}'.format(number).encode())
    digest = m.hexdigest()
    return


def test():
    NUM_OPS=400
    # for i in range(NUM_OPS):
    #     operation(i)

    test = Gorgon(operation_hash)
    test.go(num_operations=NUM_OPS, num_processes=1, num_threads=1)
    # test.print_report()
    test.go(num_operations=NUM_OPS, num_processes=2, num_threads=1)
    # test.print_report()
    test.go(num_operations=NUM_OPS, num_processes=4, num_threads=1)
    test.print_report()

if __name__ == '__main__':
    test()
