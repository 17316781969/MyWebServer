import datetime

import flask
import requests

import proxy_providers
from ads_platforms import PLATFORMS_NAME

from ..v2 import app
from .v2 import ProxyManager


@app.route("/proxy/")
@app.route("/proxy/<string:platform>")
def length_proxy(platform=None):
    if platform:
        if platform not in PLATFORMS_NAME:
            return flask.jsonify({'ret': -1, 'msg': 'platform not found'})

        platform = PLATFORMS_NAME[platform]

    if platform:
        return flask.jsonify({
            'ret': 0,
            platform.name: ProxyManager.last(platform),
        })
    else:
        ret = {
            'ret': 0,
            'dbsize': len(ProxyManager),
        }
        for platform in PLATFORMS_NAME.values():
            ret[platform.name] = ProxyManager.last(platform)

        return flask.jsonify(ret)


def hot():
    if ProxyManager:
        return flask.jsonify({'ret': 0, 'proxy': ProxyManager.get()})
    else:
        return flask.jsonify({'ret': -1, 'msg': 'run out of stock'})


@app.route("/proxy/hot")
def default_proxy():
    return hot()


@app.route("/proxy/newest", methods=['GET', 'POST'])
@app.route("/proxy/newest/<num>", methods=['GET', 'POST'])
def newest_proxy(num=20):
    return ProxyManager.get_newest(num)


def check_update_date():
    if datetime.datetime.now().hour in range(6):
        return False

    return True


from proxy_providers import wandou


@app.route("/proxy/update/wandou", methods=['GET', 'POST'])
@app.route("/proxy/update/wandou/<count>", methods=['GET', 'POST'])
def wandou_proxy(count=1):
    if not wandou.is_available():
        app.logger.info('所有套餐已经用完，请充值或忽略')

    if not check_update_date():
        return flask.jsonify(dict(ret=2, msg='不在代理使用时间'))

    if flask.request.method == 'POST':
        if flask.request.json and 'url' in flask.request.json:
            url = flask.request.json['url']
        if flask.request.json and 'times' in flask.request.json:
            times = flask.request.json['times']  # 每个代理 IP 的使用次数

    try:
        ret = wandou.fetch_proxy(count)
    except:
        return flask.jsonify(dict(ret=-1, msg='解析错误', raw=ret))

    if not ret:
        return flask.jsonify({'ret': -1, 'msg': '上游返回代理总数为空'})

    proxies = list()
    for proxy in ret:
        proxy['date_expire'] = proxy.pop('expire_time')
        date_expire = datetime.datetime.strptime(proxy['date_expire'], "%Y-%m-%d %H:%M:%S")
        date_expire = date_expire - datetime.datetime.now()
        date_expire += datetime.datetime.utcnow()
        proxy['date_expire'] = date_expire

        proxy['_from'] = 'wandou'
        proxies.append(proxy)
    success_insert_count = ProxyManager.push_multi(proxies)
    if len(proxies) != success_insert_count:
        app.logger.info(f'wandou_proxy, 获取豌豆代理IP{len(proxies)},实际插入IP{success_insert_count}')

    return flask.jsonify({
        'ret': 0, 'msg': '更新成功',
        'fetched_count': len(ret), 'inserted_count': success_insert_count
    })


@app.route("/proxy/push", methods=['POST'])
def proxy_push():
    data = flask.request.json

    for k in 'ip port _from'.split():
        if k not in data:
            return flask.jsonify({
                'ret': -1,
                'msg': '格式不对，请检查格式',
            })

    if 'date_expire' in data:
        date_expire = datetime.datetime.strptime(data['date_expire'], "%Y-%m-%d %H:%M:%S")
        date_expire = date_expire - datetime.datetime.now()
        date_expire += datetime.datetime.utcnow()

        data['date_expire'] = date_expire

    if not ProxyManager.push_single(**data):
        return flask.jsonify({
            'ret': -1,
            'msg': '插入失败，请检查格式。',
        })

    return flask.jsonify({
        'ret': 0,
        'msg': '',
    })


@app.route("/proxy/pop")
@app.route("/proxy/pop/")
@app.route("/proxy/pop/<platform>")
def proxy_pop_by_platform(platform='unknown'):
    if platform not in PLATFORMS_NAME:
        return flask.jsonify({'ret': -1, 'msg': 'platform not found'})
    platform = PLATFORMS_NAME[platform]

    proxy = ProxyManager.get(platform)

    if proxy:
        return flask.jsonify({
            'ret': 0,
            'proxy': proxy['host_port'],
            'count': proxy[platform.name] if platform.name in proxy else 0,
            'platform': platform.name
        })

    else:
        return flask.jsonify({'ret': -1, 'msg': 'run out of stock'})


@app.route("/proxy/paid/<provider>")
@app.route("/proxy/paid/<provider>/<operation>", methods="GET".split())
def proxy_get_paid_info_by_platform(provider='wandou', operation='default'):
    try:
        provider = proxy_providers.PROVIDER[provider]
    except KeyError:
        return flask.jsonify({'ret': -1, 'msg': 'platform not found'})

    try:
        operation = proxy_providers.OPERATION[operation]
    except KeyError:
        return flask.jsonify({'ret': -1, 'msg': 'operation not found'})

    if provider == proxy_providers.PROVIDER.wandou:
        from proxy_providers import wandou

        if operation == proxy_providers.OPERATION.default:
            return flask.jsonify({
                'ret': 0,
                'operation': operation.name,
                'date': wandou.fetch_order_info(),
            })


@app.route("/proxy/whitelist/<provider>")
@app.route("/proxy/whitelist/<provider>/<operation>", methods="GET".split())
def proxy_whitelist(provider='wandou', operation='add'):
    data = flask.request.json
    if data and 'ip' in data:
        if wandou.add_ip_to_white_list(data['ip']):
            return flask.jsonify({
                'ret': 0,
                'msg': f"{data['ip']}已更新到白名单"
            })
        else:
            return flask.jsonify({
                'ret': -1,
                'msg': f"{data['ip']}更新失败"
            })
    else:
        whitelist = wandou.fetch_white_list()
        return flask.jsonify({
            'ret': 0,
            'whitelist': whitelist
        })
