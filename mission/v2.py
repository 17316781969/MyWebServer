"""

使用 MongoDB 做多任务分发

"""

import os
import datetime
import random
import collections

import pymongo.errors

from MyWebServer.v2 import app, mongo
from MyWebServer.proxy.v2 import ProxyManager
from ads_platforms import PLATFORMS, PLATFORMS_NAME

###
# 使用有序字典并随机顺序
platform_values = [p for p in PLATFORMS]
random.shuffle(platform_values)


def iter_platform():
    while True:
        for p in platform_values:
            yield p


iter_platform = iter_platform()


###

class MissionManager(object):

    def __init__(self, _test=False):
        self.db = mongo.db
        self.collection = self.db.mission
        self._test = _test

        # self.collection.drop()

        self.collection.create_indexes([
            # 唯一索引，任务 URL
            pymongo.IndexModel(
                [
                    ('url', pymongo.ASCENDING),
                ],
                unique=True,
            ),
            # 任务 ID, 任务是否启用 索引
            pymongo.IndexModel(
                [
                    ('missionId', pymongo.ASCENDING),
                    ('enable', pymongo.ASCENDING),
                ],
                sparse=True,
            ),
            # 任务所属平台，当前完成数，目标数
            pymongo.IndexModel(
                [
                    ('platform', pymongo.ASCENDING),
                    ('now', pymongo.ASCENDING),
                    ('target', pymongo.DESCENDING),
                ],
            ),
            # 任务有效时间
            pymongo.IndexModel(
                [
                    ('date_expire', pymongo.ASCENDING),
                ],
                expireAfterSeconds=0,
            ),
            # 代理插入时间，以确保任务最长有效期为 12 小时
            pymongo.IndexModel(
                [
                    ('date_insert', pymongo.DESCENDING),
                ],
                expireAfterSeconds=60 * 60 * 12,
            ),
        ])

    def __parse_mission_format(self, mission):
        for k in 'url missionId target platform from'.split():
            if k not in mission:
                return False

        try:
            mission['target'] = int(mission['target'])
            mission['missionId'] = int(mission['missionId'])
            mission['platform'] = PLATFORMS_NAME \
                .get(mission['platform'], PLATFORMS.unknown)
        except:
            return False

        mission['platform'] = mission['platform'].name
        # mission['expire'] = self.datetime_tomorrow_morning_3_am
        mission['date_insert'] = datetime.datetime.utcnow()
        return mission

    def publish(self, **mission):
        """
        发布任务

        :param missions:
        :return:
        """
        mission: dict = self.__parse_mission_format(mission)

        if not mission:
            return False

        mission.setdefault('enable', False)  # 任务默认状态不启动

        return self.collection.update_one(
            dict(missionId=mission.pop('missionId'), url=mission.pop('url')),
            {"$set": mission},
            upsert=True,
        )

    def modify(self, **mission):
        mission: dict = self.__parse_mission_format(mission)

        if not mission:
            return False

        return self.collection.update_one(
            dict(id=mission.pop('missionId'), url=mission.pop('url')),
            {"$set": mission},
            upsert=True,
        )

    def exists(self, *args):
        """
        (id, url)

        :param args:
        :return:
        """

        find = {"$or": []}

        for id, url in args:
            find['$or'].append({'missionId': id, 'url': url})

        results = list(self.collection.find(find, {'_id': 0, 'missionId': 1, 'url': 1}))

        return [{'missionId': id, 'url': url} in results for id, url in args]

    @property
    def datetime_tomorrow_morning_3_am(self):
        now = datetime.datetime.utcnow()
        tomorrow = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if now.hour > 2:
            tomorrow += datetime.timedelta(days=1)

        return tomorrow

    def last(self, platform=PLATFORMS.unknown):
        return self.collection.count_documents({'platform': platform.name})

    def perform_specific(self, platform=PLATFORMS.unknown):
        """
        执行任务

        :return:
        """
        return self.collection.find_one_and_update(
            filter={
                "platform": platform.name,
                "$or": [
                    {"now": None},
                    {"$where": "this.target > this.now"},
                ],
                "enable": True,
            },
            update={'$inc': {'now': 1}},
            projection={
                '_id': False,
                'missionId': True,
                'url': True,
                'platform': True,
                'from': True,
                'operations': True,
                'device_ratio': True,
            },
            sort=[
                ("now", pymongo.ASCENDING),
            ]
        )

    def perform_ordered(self, check=True):
        """
        按平台顺序依次叠加

        :return:
        """

        for _ in range(len(PLATFORMS)):

            platform = next(iter_platform)
            if check:
                if not ProxyManager.is_exists(platform):
                    continue
            mission = self.perform_specific(platform)
            if mission:
                return mission

        return None

    def enable_perform_ordered(self, check=True):
        """
        直接到数据库取执行任务最少的平台

        :return:
        """
        platform = self.mission_enable_platform()
        if platform:
            mission = self.perform_specific(platform)
            if mission:
                return mission

        return None

    def reset_all(self):
        self.collection.update_many({'enable': True}, {'$set': {'now': 0}})

    def __len__(self):
        return self.collection.estimated_document_count()

    def __bool__(self):
        return len(self) > 0

    def disable(self, object_id):
        self.collection.find_one_and_update({'_id': object_id}, {'$set': {'enable': False}})

    def enable(self, object_id):
        self.collection.find_one_and_update({'_id': object_id}, {'$set': {'enable': True}})

    def get(self, object_id):
        return self.collection.find_one({'_id': object_id})

    def mission_enable_total(self):
        datas = []
        summary = {'_id': 'summary', 'target': 0, 'now': 0, 'surplus': 0}
        cursor = self.collection.aggregate([
            {'$match': {'enable': True}},
            {'$group': {'_id': '$platform', 'target': {'$sum': '$target'}, 'now': {'$sum': '$now'},
                        'surplus': {'$sum': {'$subtract': ['$target', '$now']}}}},
            # {'$match': {'surplus': {'$gt': 0}}},
            # {'$sort': {'now': 1}}
        ])
        for data in cursor:
            summary['target'] += data['target']
            summary['now'] += data['now']
            summary['surplus'] += data['surplus']
            if data['surplus'] > 0:
                datas.append(data)
        datas.append(summary)

        return datas

    def mission_enable_platform(self):
        cursor = self.collection.aggregate([
            {'$match': {'enable': True}},
            {'$group': {'_id': '$platform', 'target': {'$sum': '$target'}, 'now': {'$sum': '$now'},
                        'surplus': {'$sum': {'$subtract': ['$target', '$now']}}}},
            {'$match': {'surplus': {'$gt': 0}}},
            {'$sort': {'now': 1}}
        ])

        for data in cursor:
            return PLATFORMS[data['_id']]
        return None


MissionManager = MissionManager()
