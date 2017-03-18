"""
Modules
=======

Module as in MVC.
"""

from pymongo import MongoClient


def get_mongo_client(factory: str) -> MongoClient:
    """
    Create a MongoClient instance based on the given `factory` name.

    :param factory: name of the factory
    :return: MongoClient instance
    """
    if factory == 'local':
        return MongoClient('localhost')
    elif factory == 'docker':
        return MongoClient('mongo')
    else:
        raise ValueError('unknown factory')
