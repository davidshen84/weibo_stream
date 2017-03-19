"""
WeiboCrawler
============

A simple crawler.
"""

from pymongo.collection import Collection
from tornado.ioloop import PeriodicCallback
from tornado.log import app_log

from modules import WeiboClient


class WeiboCrawler(PeriodicCallback):
    """
    Periodical callback to crawl weibo statuses.

    :param callback_time: Callback interval in million second.
    """

    def __init__(self, weibo_client: WeiboClient, mongo_collection: Collection, callback_time: int):
        super().__init__(self.async_crawler, callback_time)
        self._weibo_client = weibo_client
        self._mongo_collection = mongo_collection

    async def async_crawler(self):
        try:
            statuses = await self._weibo_client.public_timeline()
            if statuses:
                results = self._mongo_collection.insert_many(statuses)
                app_log.debug(f'got statuses count: {len(results.inserted_ids)}')
            else:
                app_log.warn('No new status received.')
        except Exception as e:
            app_log.exception(e)