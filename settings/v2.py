import datetime

import pymongo.errors

from ..v2 import mongo


class SettingsManager(object):
    def __init__(self):
        self.collection = mongo.db.settings

        self.collection.create_indexes([
            # 设置对应的机型
            pymongo.IndexModel(
                [
                    ('hostname', pymongo.ASCENDING),
                ],
                unique=True,
            ),
        ])

    def get(self, setting_name, hostname='unknown'):
        ret = self.collection.find_one(
            filter={
                'hostname': hostname,
            },
            projection={
                '_id': False,
                setting_name: True,
            }
        )
        return ret[setting_name] if ret else None

    def set(self, setting_name, setting_value, hostname='unknown'):
        ret = self.collection.find_one_and_update(
            filter={
                "hostname": hostname,
            },
            update={
                "$set": {
                    setting_name: setting_value,
                    'date_update': datetime.datetime.utcnow()
                }
            },
            projection={
                '_id': False,
                setting_name: True,
            },
            upsert=True
        )
        return ret


SettingsManager = SettingsManager()
