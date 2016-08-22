"""
Weibo Streaming
===============

Turn `weibo`_ statues into a HTTP Stream.

- Please refer to *weibo* `API documents`_ for detail weibo statuses API
- Please refer to `chunked`_ encoding for how HTTP streaming implementation specification

.. _weibo: http://www.weibo.com
.. _API documents: http://open.weibo.com/wiki/%E5%BE%AE%E5%8D%9AAPI
.. _chunked: https://en.wikipedia.org/wiki/Chunked_transfer_encoding
"""
import logging

from tornado.escape import json_decode
from tornado.httpclient import AsyncHTTPClient


class Fib(object):
    """
    Generate Fibonacci sequence

    >>> fib = Fib()
    >>> fib.next()
    1

    >>> fib.next()
    1

    >>> fib.next()
    2
    >>> fib.next()
    3
    >>> fib.next()
    5
    >>> fib.reset()
    >>> fib.next()
    1
    """

    def __init__(self):
        self._counter = 0
        self._a = 1
        self._b = 1
        self._c = -1

    def __iter__(self):
        return self

    def __next__(self):
        self._counter += 1
        if self._counter <= 2:
            return 1
        else:
            self._c = self._a + self._b
            self._a = self._b
            self._b = self._c

            return self._c

    def next(self):
        return self.__next__()

    def reset(self):
        self._counter = 0
        self._a = 1
        self._b = 1
        self._c = -1


app_logger = logging.getLogger('tornado.application')


class WeiboClient(object):
    _weibo_public_timeline_url = 'https://api.weibo.com/2/statuses/public_timeline.json?access_token={}'

    def __init__(self, access_token):
        self._http_client = AsyncHTTPClient()
        self._access_token = access_token
        self.last_id = 0

    def public_timeline(self):
        response = yield self._http_client.fetch(WeiboClient._weibo_public_timeline_url.format(self._access_token))

        if response.code == 200:
            json_body = json_decode(response.body)
            statuses = [s for s in json_body['statuses'] if s['id'] > self.last_id]

            if len(statuses) > 0:
                self.last_id = statuses[0]['id']

            return statuses
        else:
            app_logger.error('weibo api respond {}'.format(response.code))
            return []
