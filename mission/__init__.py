import flask

from ads_platforms import PLATFORMS, PLATFORMS_NAME, PLATFORMS_OPERATIONS

from ..v2 import app
from .v2 import MissionManager
from ..proxy.v2 import ProxyManager


###

def get_operations(platform_name):
    platform = PLATFORMS_NAME[platform_name]

    if platform in PLATFORMS_OPERATIONS:
        return PLATFORMS_OPERATIONS[platform]
    return None


def perform():
    if MissionManager:
        mission = MissionManager.perform_ordered(check=True)
        if mission:
            platform = mission.pop('platform')
            proxy = ProxyManager.get(PLATFORMS_NAME[platform])
            if proxy:
                data = {
                    'ret': 0,
                    'missionId': mission.pop('missionId'),
                    'url': mission.pop('url'),
                    'platform': platform,
                    'from': mission.pop('from'),
                    'proxy': proxy['host_port'],
                    'count': proxy[platform] if platform in proxy else 0,
                }
                if 'operations' in mission:
                    data['operations'] = mission.pop('operations')
                else:
                    data['operations'] = get_operations(data['platform'])
                if 'device_ratio' in mission:
                    data['device_ratio'] = mission.pop('device_ratio')
                data['else'] = mission
                return data

    return {'ret': -1, 'msg': 'run out of stock'}


def enable_perform():
    if MissionManager:
        mission = MissionManager.enable_perform_ordered()
        if mission:
            platform = mission.pop('platform')
            proxy = ProxyManager.get(PLATFORMS_NAME[platform])
            url = mission.pop('url')
            if url.find("from") == -1:
                if url.find("?") > -1:
                    url += url + '&from=singlemessage'
                else:
                    url += url + '?from=singlemessage'
            url = url.replace("&amp;", "&")
            if proxy:
                data = {
                    'ret': 0,
                    'missionId': mission.pop('missionId'),
                    'url': url,
                    'platform': platform,
                    'from': mission.pop('from'),
                    'proxy': proxy['host_port'],
                    'count': proxy[platform] if platform in proxy else 0,
                }
                if 'operations' in mission:
                    data['operations'] = mission.pop('operations')
                else:
                    data['operations'] = get_operations(data['platform'])
                if 'device_ratio' in mission:
                    data['device_ratio'] = mission.pop('device_ratio')
                data['else'] = mission
                return data

    return {'ret': -1, 'msg': 'run out of stock'}


@app.route("/mission/perform")
def perform_mission():
    mission = enable_perform()
    if not mission['ret']:
        from fake_identity.HereNowWechat import HereNowWechat
        if 'device_ratio' in mission:
            mission['user_agent'] = HereNowWechat.random_ratio_choice(device_ratio=mission['device_ratio'])
        else:
            mission['user_agent'] = HereNowWechat.random
        if mission['platform'] == 'vflow':
            from fake_identity.HereNoSpider import HereNoSpider
            mission['user_agent'] = HereNoSpider.random
    return flask.jsonify(mission)


@app.route("/mission/enable_perform")
def enable_perform_mission():
    mission = enable_perform()
    if not mission['ret']:
        from fake_identity.HereNowWechat import HereNowWechat
        if 'device_ratio' in mission:
            mission['user_agent'] = HereNowWechat.random_ratio_choice(device_ratio=mission['device_ratio'])
        else:
            mission['user_agent'] = HereNowWechat.random
        if mission['platform'] == 'vflow':
            from fake_identity.HereNoSpider import HereNoSpider
            mission['user_agent'] = HereNoSpider.random
    return flask.jsonify(mission)


@app.route("/mission/publish", methods=['POST'])
def publish_mission():
    data = flask.request.json

    ret = MissionManager.publish(**data)
    if not ret:
        return flask.jsonify({'ret': -1, 'msg': 'POST data format error!'})

    return flask.jsonify({'ret': 0, 'msg': 'Mission publish success'})


@app.route("/mission/")
def mission_info():
    j = {
        'ret': 0,
        'total': len(MissionManager),
    }
    for plat in PLATFORMS:
        j[plat.name] = MissionManager.last(plat)
    return flask.jsonify(j)


@app.route("/mission/enable/total")
def mission_enable_total():
    data = MissionManager.mission_enable_total()
    return flask.jsonify({
        'ret': 0,
        'data': data,
    })


@app.route("/mission/check")
def mission_master_check():
    """从服务器中同步任务数据"""
    import pymongo.errors

    try:
        client = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
        session = client.start_session()
    except pymongo.errors.ServerSelectionTimeoutError:
        return flask.jsonify({'ret': 1001, 'msg': '服务器可能中断，连接失败。'})

    session.end_session()
    return flask.jsonify({'ret': 0, 'msg': 'okay'})
