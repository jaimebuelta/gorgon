''' Quick test to check functionality on Gorgon '''
from gorgon import Gorgon
import requests


def operation(number):
    result = requests.get('http://localhost')
    return result.status_code


def test():

    test = Gorgon(operation)
    test.go(num_operations=40000, num_processes=10, num_threads=10,
            random_delay=False)


if __name__ == '__main__':
    test()
