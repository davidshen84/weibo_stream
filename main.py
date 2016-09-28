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

from tornado import gen
from tornado import ioloop
from tornado import web
from tornado.escape import json_encode, json_decode
from tornado.httpclient import HTTPError
from tornado.options import define, options

from util import FibonacciSequence, remote_ip, CircularList
from weibo_client import WeiboClient

access_logger = logging.getLogger('tornado.access')
app_logger = logging.getLogger('tornado.application')

# chunked transfer encoding delimiter
CRLF = '\r\n'

# define tornado command line arguments
define('weibo_access_tokens', multiple=True)
weibo_access_tokens = None
define('debug', default=False)


class MainHandler(web.RequestHandler):
    def data_received(self, chunk):
        raise NotImplementedError()

    def get(self):
        self.write('''
        access /public_timeline to get a weibo public status stream
        ''')


class PublicTimelineHandler(web.RequestHandler):
    """
    Handles GET /public_timeline request.
    """

    def data_received(self, chunk):
        raise NotImplementedError()

    @gen.coroutine
    def get(self):
        client = WeiboClient(next(weibo_access_tokens))
        access_logger.info('start streaming to %s', remote_ip(self.request))
        self.set_header('transfer-encoding', 'chunked')
        self.set_header('content-type', 'application/json; charset=utf-8')
        fib = FibonacciSequence(start_from=5)

        while True:
            try:
                statuses = yield client.public_timeline()
                if not self.request.connection.stream.closed():
                    statuses_count = len(statuses)
                    if statuses_count > 0:
                        for s in statuses:
                            chunked = json_encode(s)
                            chunked_size = len(chunked)
                            self.write('{:x}{}'.format(chunked_size + 1, CRLF))
                            self.write('{}\n{}'.format(chunked, CRLF))
                        self.flush()
                        fib.reset()
                        sleep_duration = next(fib)
                    else:
                        sleep_duration = next(fib)
                        app_logger.warn('no new statuses')

                    app_logger.info('sleep %d seconds', sleep_duration)
                    yield gen.sleep(sleep_duration)
                else:
                    break
            except HTTPError as e:
                if e.code == 403:
                    json_body = json_decode(e.response.body)
                    if json_body['error_code'] == 10023:
                        app_logger.warn('access token is blocked')
                        yield gen.sleep(30 * 60)
                        client.set_token(next(weibo_access_tokens))
                else:
                    app_logger.error('weibo api responded %s, %s, %s',
                                     e.code, e.message, e.response.body if e.response else 'empty response')
                    app_logger.warn('stream closed')
                    self.write('0' + CRLF * 2)
                    break

                if self.request.connection.stream.closed():
                    break

        access_logger.info('stopped streaming to %s', remote_ip(self.request))


def on_connection_close(self):
    access_logger.info('close connection to %s', remote_ip(self.request))
    self.finish()


if __name__ == '__main__':
    options.parse_command_line()
    weibo_access_tokens = CircularList(options.weibo_access_tokens)
    app = web.Application([
        (r'/', MainHandler),
        (r'/public_timeline', PublicTimelineHandler)
    ],
        debug=options.debug)
    # listen to default HTTP port
    app.listen(80)
    ioloop.IOLoop.current().start()
