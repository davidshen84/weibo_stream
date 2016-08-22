import logging

from tornado import gen
from tornado import ioloop
from tornado import web
from tornado.escape import json_encode
from tornado.options import define, options

from . import Fib, WeiboClient

weibo_public_timeline_url = 'https://api.weibo.com/2/statuses/public_timeline.json?access_token={}'
access_logger = logging.getLogger('tornado.access')
app_logger = logging.getLogger('tornado.application')
sleep_duration_origin = 3
sleep_duration_increase_factor = 2

# chunked transfer encoding delimiter
CRLF = '\r\n'

# define tornado command line arguments
define('weibo_access_token')
define('debug', default=False)


def remote_ip(request):
    return request.headers.get('X-Real-IP') or request.remote_ip


# noinspection PyAbstractClass
class MainHandler(web.RequestHandler):
    def get(self):
        self.write('''
        access /public_timeline to get a weibo public status stream
        ''')


# noinspection PyAbstractClass
class PublicTimelineHandler(web.RequestHandler):
    @gen.coroutine
    def get(self):
        client = WeiboClient(options.weibo_access_token)
        access_logger.info('start streaming to {}'.format(remote_ip(self.request)))
        self.set_header('transfer-encoding', 'chunked')
        self.set_header('content-type', 'application/json; charset=utf-8')
        fib = Fib()

        while True:
            statuses = yield client.public_timeline()
            if not self.request.connection.stream.closed():
                statuses_count = len(statuses)
                if statuses_count > 0:
                    app_logger.info('received {} new statuses'.format(statuses_count))
                    for s in statuses:
                        chunked = json_encode(s)
                        chunked_size = len(chunked)
                        self.write('{:x}{}'.format(chunked_size + 1, CRLF))
                        self.write('{}\n{}'.format(chunked, CRLF))
                    self.flush()
                    app_logger.info('last id updated to {}'.format(client.last_id))
                    fib.reset()
                    sleep_duration = fib.next()
                else:
                    sleep_duration = fib.next()
                    app_logger.warn('no new statuses (sleeping {} seconds)'.format(sleep_duration))

                yield gen.sleep(sleep_duration)
            else:
                # access_logger.info('stop streaming to {}'.format(remote_ip(self.request))
                return
                # self.write('0' + CRLF)
                # self.write(CRLF)

    def on_connection_close(self):
        access_logger.info('close connection to {}'.format(remote_ip(self.request)))
        self.finish()


if __name__ == '__main__':
    options.parse_command_line()

    app = web.Application([
        (r'/', MainHandler),
        (r'/public_timeline', PublicTimelineHandler)
    ],
        debug=options.debug)
    # listen to default HTTP port
    app.listen(80)
    ioloop.IOLoop.current().start()
