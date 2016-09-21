import logging

from tornado import gen
from tornado.escape import json_decode
from tornado.httpclient import AsyncHTTPClient

logger = logging.getLogger('weibo_stream')


class WeiboClient(object):
    """A simple Weibo client

    *Instances are not thread safe.*

    :param access_token: Weibo access token
    """

    _weibo_public_timeline_url = 'https://api.weibo.com/2/statuses/public_timeline.json?access_token={}&count=50'

    def __init__(self, access_token: str):
        self._http_client = AsyncHTTPClient()
        self._access_token = access_token
        self._last_id = 0

    @gen.coroutine
    def public_timeline(self) -> list:
        """Returns a **Future** of a list of statuses from the public timeline API.

        * If the remote API response none 200 status code, the status code will be logged.
        * If the remote API raise exception, it will be raised to upstream.

        :return: Weibo statuses on public timeline.
        """
        response = yield self._http_client.fetch(WeiboClient._weibo_public_timeline_url.format(self._access_token))

        if response.code == 200:
            json_body = json_decode(response.body)
            statuses = [s for s in json_body['statuses'] if s['id'] > self._last_id]
            statuses_count = len(statuses)

            if statuses_count > 0:
                logger.info('received %s new statuses', statuses_count)
                self._last_id = statuses[0]['id']
                logger.info('last id updated to %s', self._last_id)

            return statuses
        else:
            logger.error('weibo api responded status %s', response.code)
            return []

    def set_token(self, access_token: str):
        """
        Set the Weibo access token to use.

        :type access_token: str
        :param access_token: Weibo access token
        """
        self._access_token = access_token
