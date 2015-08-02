''' Quick test to check functionality on Gorgon '''
from gorgon import Gorgon
from time import sleep
import requests


def operation(number):
    result = 1 + ((number * 2) % 5)
    sleep(0.002 * result)
    result = requests.get('http://localhost')
    return result.status_code


def test():

    test = Gorgon(operation)
    test.go(num_operations=40000, num_processes=10, num_threads=10)


if __name__ == '__main__':
    test()
