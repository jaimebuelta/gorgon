''' Quick test to check functionality on Gorgon '''
from gorgon import Gorgon
from random import randint


def callback(previous_result):
    if randint(0, 10) > 5:
        return {
            'url': 'http://localhost/',
            'method': 'GET',
        }

    return None


def test(url):
    profiles = {
        1: {
            'url': url,
            'method': 'GET',
            'callback': callback,
        }
    }

    test = Gorgon(profiles)
    test.go(num_requests=5000)


if __name__ == '__main__':
    test(url='http://localhost')
