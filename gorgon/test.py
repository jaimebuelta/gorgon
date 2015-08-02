''' Quick test to check functionality on Gorgon '''
from gorgon import Gorgon
import requests
import hashlib

def operation(number):
    result = requests.get('http://localhost')
    return result.status_code


def operation(number):
    m = hashlib.sha512()
    for _ in range(4000):
        m.update('TEXT {}'.format(number).encode())
    digest = m.hexdigest()
    return digest[0]


def test():
    NUM_OPS=4
    # for i in range(NUM_OPS):
    #     operation(i)

    test = Gorgon(operation)
    test.go(num_operations=NUM_OPS, num_processes=2, num_threads=3,
            random_delay=True)


if __name__ == '__main__':
    test()
