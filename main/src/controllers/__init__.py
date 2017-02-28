"""
Controllers
===========

"""
from threading import Lock

from tornado import gen
from tornado.escape import json_encode, json_decode
from tornado.httpclient import HTTPError
from tornado.httputil import HTTPServerRequest
from tornado.ioloop import IOLoop
from tornado.locks import Event
from tornado.log import access_log, app_log
from tornado.web import RequestHandler

from modules.util import FibonacciSequence

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
                                                self.reverse_url('job', '')])


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
            super().finish(chunk='0' + CRLF * 2)

        app_log.info('stream closed.')

    def on_connection_close(self):
        access_log.info('close connection to %s.', remote_ip(self.request))
        super().on_connection_close()


class WeiboStatusCrawlerHandler(RequestHandler):
    """
    Handles Weibo status crawler status.
    """

    _crawler_initialized = False
    _crawler_initialize_lock = Lock()
    _crawler_wait_seconds = 10
    _event = Event()

    @staticmethod
    async def _async_crawler(weibo_client, collection):
        """
        Long run background job to crawl weibo status.

        :return: None
        """
        app_log.info('async_weibo_status_crawler started.')
        while True:
            await WeiboStatusCrawlerHandler._event.wait()
            try:
                statuses = await weibo_client.public_timeline()
                results = collection.insert_many(statuses)
                app_log.debug('got statuses count: {}'.format(len(results.inserted_ids)))
            except TypeError:
                app_log.warn("sleep longer...zzZ")
                await gen.sleep(WeiboStatusCrawlerHandler._crawler_wait_seconds)
            except Exception as e:
                app_log.exception(e)

            await gen.sleep(WeiboStatusCrawlerHandler._crawler_wait_seconds)

    def initialize(self, weibo_access_tokens, weibo_client_factory, mongo_client):
        statuses_collection = mongo_client['weibo']['statuses']

        if not self._crawler_initialized and WeiboStatusCrawlerHandler._crawler_initialize_lock.acquire():
            if not self._crawler_initialized:
                IOLoop.current().spawn_callback(WeiboStatusCrawlerHandler._async_crawler,
                                                weibo_client_factory(next(weibo_access_tokens)),
                                                statuses_collection)
                WeiboStatusCrawlerHandler._crawler_initialized = True
            WeiboStatusCrawlerHandler._crawler_initialize_lock.release()

    def data_received(self, chunk):
        raise NotImplementedError()

    def get(self, action):
        unknown_action = None
        if action == 'start' and not self._event.is_set():
            self._event.set()
        elif action == 'stop' and self._event.is_set():
            self._event.clear()
        elif action != '':
            unknown_action = action

        self.render('weibo_crawler_status.html', unknown_action=unknown_action, is_set=self._event.is_set())
