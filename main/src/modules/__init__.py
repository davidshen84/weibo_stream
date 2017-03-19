"""
Modules
=======

Module as in MVC.
"""

from pymongo import MongoClient
from pymongo.collection import Collection

from modules.weibo_client import WeiboClient
from modules.weibo_crawler import WeiboCrawler


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
