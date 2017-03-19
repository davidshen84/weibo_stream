"""
Modules
=======

Module as in MVC.
"""

from pymongo import MongoClient
from pymongo.collection import Collection
from tornado.ioloop import PeriodicCallback
from tornado.log import app_log

from modules.weibo_client import WeiboClient


def get_mongo_collection(factory: str) -> Collection:
    """
    Create a MongoClient instance based on the given `factory` name.

    :param factory: name of the factory
    :return: MongoClient instance
    """
    if factory == 'local':
        return MongoClient('localhost')['weibo']['statuses']
    elif factory == 'docker':
        return MongoClient('mongo')['weibo']['statuses']
    elif factory == 'daocloud':
        from os import environ
        mongodb_connection = environ['MONGODB_CONNECTION']
        mongodb_instance_name = environ['MONGODB_INSTANCE_NAME']

        return MongoClient(f'mongodb://{mongodb_connection}')[mongodb_instance_name]['statuses']
    else:
        raise ValueError('unknown factory')


class WeiboCrawler(PeriodicCallback):
    """
    Manages the background crawl task.

    """

    def __init__(self, weibo_client: WeiboClient, mongo_collection: Collection, callback_time: int):
        super().__init__(self.async_crawler, callback_time)
        self._weibo_client = weibo_client
        self._mongo_collection = mongo_collection

    async def async_crawler(self):
        try:
            statuses = await self._weibo_client.public_timeline()
            results = self._mongo_collection.insert_many(statuses)
            app_log.debug(f'got statuses count: {len(results.inserted_ids)}')
        except TypeError:
            app_log.warn("No statuses received.")
        except Exception as e:
            app_log.exception(e)
