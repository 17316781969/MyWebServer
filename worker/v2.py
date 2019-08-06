import datetime

import pymongo

from ..v2 import mongo


class WorkerManager(object):
    def __init__(self):
        self.collection = mongo.db.workers

        self.collection.create_indexes([
            # 设置对应的机型
            pymongo.IndexModel(
                [
                    ('hostname', pymongo.ASCENDING),
                ],
                unique=True,
            ),
            # # Worker 插入时间，自动清除 6 分钟内没有响应的 Worker
            # pymongo.IndexModel(
            #     [
            #         ('date_update', pymongo.ASCENDING),
            #     ],
            #     expireAfterSeconds=60 * 6,
            # ),
        ])

    def alive(self, hostname, **kwargs):
        kwargs.setdefault('date_update', datetime.datetime.utcnow())
        ret = self.collection.find_one_and_update(
            filter={
                "hostname": hostname,
            },
            update={
                "$set": kwargs
            },
            projection={
            },
            upsert=True
        )
        return ret

    def breath(self, hostname):
        ret = self.collection.find_one(
            filter={
                "hostname": hostname,
            },
        )
        return ret

    def set_num_threads(self, target, surplus):
        num = 40
        if 0 < surplus < 500 or target < 2000 or target > 5500:
            return False

        if target < 2500:
            num = 45
        elif 2500 <= target < 4000:
            num = 55
        elif 4000 <= target < 5000:
            num = 65
        elif 5000 <= target:
            num = 75
        ret = self.collection.update_many(
            {},
            {"$set": {"length_browsers_full": num}}
        )
        return ret


WorkerManager = WorkerManager()
