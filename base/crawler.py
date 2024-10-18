import requests


def request(URL):
    return requests.get(URL, timeout=(5, 10)).content.decode('utf-8')
