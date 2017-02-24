"""
Controllers
===========

"""
from tornado import gen
from tornado.escape import json_encode, json_decode
from tornado.httpclient import HTTPError
from tornado.httputil import HTTPServerRequest
from tornado.log import access_log, app_log
from tornado.web import RequestHandler

from modules import FibonacciSequence

# chunked transfer encoding delimiter
CRLF = '\r\n'


def remote_ip(request: HTTPServerRequest) -> str:
    """Try to extract the client IP from the header, or the request.

    :param request: `tornado.httputil.HTTPServerRequest`
    :return: client IP address
    """
    return request.headers.get('X-Real-IP') or request.remote_ip


class DefaultHandler(RequestHandler):
    """
    Handles everything, so there's won't be 404 error.
    """

    def data_received(self, chunk):
        raise NotImplementedError()

    def get(self):
        # self.write('''
        # access {} to get a weibo public status stream
        # '''.format(self.reverse_url('default')))
        self.render("default.html", interfaces=[self.reverse_url('public_timeline'),
                                                self.reverse_url('job')])


class PublicTimelineHandler(RequestHandler):
    """
    Handles Weibo public timeline streaming.
    """

    _weibo_access_tokens = None
    _weibo_client_factory = None

    def initialize(self, weibo_access_tokens, weibo_client_factory):
        self._weibo_access_tokens = weibo_access_tokens
        self._weibo_client_factory = weibo_client_factory

    def data_received(self, chunk):
        raise NotImplementedError()

    async def get(self):
        client = self._weibo_client_factory(next(self._weibo_access_tokens))
        access_log.info('start streaming to %s', remote_ip(self.request))
        self.set_header('transfer-encoding', 'chunked')
        self.set_header('content-type', 'application/json; charset=utf-8')
        fib = FibonacciSequence(start_from=5)

        while True:
            try:
                statuses = await client.public_timeline()
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
                        app_log.warn('no new statuses.')

                    app_log.info('sleep %d seconds.', sleep_duration)
                    await gen.sleep(sleep_duration)
                else:
                    break
            except HTTPError as e:
                if e.code == 403:
                    json_body = json_decode(e.response.body)
                    if json_body['error_code'] == 10023:
                        app_log.warn('access token is blocked.')
                        await gen.sleep(30 * 60)
                        client.set_token(next(self._weibo_access_tokens))
                else:
                    app_log.error('weibo api responded %s, %s, %s.',
                                  e.code, e.message, e.response.body if e.response else 'empty response')

                    break

            except ConnectionError as e:
                app_log.exception(e.strerror, e, exc_info=True)
                break

        access_log.info('stopped streaming to %s.', remote_ip(self.request))
        self.finish()

    def finish(self, chunk=None):
        if not self.request.connection.stream.closed():
            self.finish(chunk='0' + CRLF * 2)

        app_log.info('stream closed.')
        super().finish(chunk)

    def on_connection_close(self):
        access_log.info('close connection to %s.', remote_ip(self.request))
        super().on_connection_close()
