"""

使用 MongoDB 做代理 IP 分发

"""

import os
import datetime
import random

import flask
import requests
import pymongo
from pymongo.errors import BulkWriteError

from ads_platforms import PLATFORMS, PLATFORMS_NAME, PLATFORMS_IP_LIMIT, DEFAULT_IP_LIMIT

from MyWebServer.v2 import app, mongo


class ProxyManager(object):

    def __init__(self):
        self.db = mongo.db
        self.collection = self.db.proxy
        self.collection.create_indexes([
            # 代理的键值对
            pymongo.IndexModel(
                [
                    ('host_port', pymongo.ASCENDING),
                ],
                unique=True,
            ),
            # 代理有效时间
            pymongo.IndexModel(
                [
                    ('date_expire', pymongo.ASCENDING),
                ],
                expireAfterSeconds=0,
            ),
            # 代理插入时间，并确保最多存留 24 小时
            pymongo.IndexModel(
                [
                    ('date_insert', pymongo.DESCENDING),
                ],
                expireAfterSeconds=60 * 60 * 24,
            ),
        ])

    def get(self, platform=PLATFORMS.unknown):
        ret = self.collection.find_one_and_update(
            filter={
                "$or": [
                    {platform.name: None},
                    {platform.name: {"$lt": PLATFORMS_IP_LIMIT.get(platform, DEFAULT_IP_LIMIT)}}
                ],
            },
            update={
                "$inc": {platform.name: 1},
            },
            projection={
                '_id': False,
                'host_port': True,
                platform.name: True,
            },
            sort=[
                ('date_insert', pymongo.DESCENDING),
            ]
        )
        return ret if ret else None

    def get_newest(self, num):
        ret = self.collection.find(
            filter={},
            projection={
                '_id': False,
                'host_port': True,
            },
            sort=[
                ('$natural', pymongo.DESCENDING),
            ]
        ).limit(int(num))
        return random.choice([d['host_port'] for d in ret if d])

    def last(self, platform=PLATFORMS.unknown):
        return self.collection.count_documents({
            "$or": [
                {platform.name: None},
                {platform.name: {"$lt": PLATFORMS_IP_LIMIT.get(platform, DEFAULT_IP_LIMIT)}}
            ],
        })

    def is_exists(self, platform=PLATFORMS.unknown):
        """
        分配给平台的代理 IP 是否还存在

        :param platform:
        :return:
        """

        return True if self.collection.find_one({
            "$or": [
                {platform.name: None},
                {platform.name: {"$lt": PLATFORMS_IP_LIMIT.get(platform, DEFAULT_IP_LIMIT)}}
            ],
        }) else False

    def push_single(self, ip, port, _from, date_expire: datetime.datetime):
        """


        :param ip:
        :param port:
        :param date_expire: 失效时间
        :param _from: 代理来源
        :return:
        """

        proxy = {
            'host_port': f"{ip}:{port}",
            'from': _from,
            'date_insert': datetime.datetime.utcnow(),
        }
        if isinstance(date_expire, datetime.datetime):
            proxy['date_expire'] = date_expire

        return self.collection.insert_one(proxy)

    def push_multi(self, proxies: list):
        """

        :param proxies:
        :return:
        """
        try:
            self.collection.insert_many([
                {
                    'host_port': f"{proxy['ip']}:{proxy['port']}",
                    'date_insert': datetime.datetime.utcnow(),
                    'date_expire': proxy['date_expire'],
                    'from': proxy['_from'],
                } for proxy in proxies
            ], ordered=False)
            return len(proxies)
        except BulkWriteError as e:
            return e._OperationFailure__details['nInserted']

    def __len__(self):
        return self.collection.estimated_document_count()

    def __bool__(self):
        return len(self) > 0


ProxyManager = ProxyManager()
