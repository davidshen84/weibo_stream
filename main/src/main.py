"""
Weibo Streaming
===============

Wraps `weibo`_ public statues API into a stream like API.

- Please refer to *weibo* `API documents`_ for details
- Please refer to `chunked`_ encoding for how HTTP streaming implementation specification

.. _weibo: http://www.weibo.com
.. _API documents: http://open.weibo.com/wiki/%E5%BE%AE%E5%8D%9AAPI
.. _chunked: https://en.wikipedia.org/wiki/Chunked_transfer_encoding
"""

from tornado import web
from tornado.ioloop import IOLoop
from tornado.options import define, options

from controllers import app_log, DefaultHandler, PublicTimelineHandler, WeiboStatusCrawlerHandler
from modules import WeiboClient, WeiboCrawler, get_mongo_collection
from modules.util import CircularList

define('listen', default=80)
define('weibo_access_tokens', multiple=True)
define('mongo_env', default='local')
define('crawler_sleep_time', default=60)
define('debug', default=False)

if __name__ == '__main__':
    options.parse_command_line()
    weibo_access_tokens = CircularList(options.weibo_access_tokens)
    weibo_client = WeiboClient(next(weibo_access_tokens))
    mongo_collection = get_mongo_collection(options.mongo_env)
    weibo_crawler = WeiboCrawler(weibo_client, mongo_collection, options.crawler_sleep_time * 1000)

    app = web.Application([
        (r'/v1/public_timeline', PublicTimelineHandler,
         {'weibo_access_tokens': CircularList(options.weibo_access_tokens),
          'weibo_client_factory': lambda token: WeiboClient(token)}, 'public_timeline'),
        (r'/v2/job/(?P<action>\w*)', WeiboStatusCrawlerHandler,
         {'weibo_crawler': weibo_crawler}, 'job'),
        (r'/.*', DefaultHandler)],
        debug=options.debug)
    app.listen(options.listen)
    try:
        IOLoop.current().start()
    except KeyboardInterrupt:
        app_log.info('bye')
