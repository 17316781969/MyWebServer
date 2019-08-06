from MyWebServer.v2 import app

import os

import flask

__dir__ = os.path.dirname(__file__)
PATH_DIST = os.path.join(
    __dir__,
    'dist',
)


@app.route("/admin")
@app.route("/admin/<path:subpath>")
def index_admin(subpath=None):
    if subpath and subpath.startswith('api/'):
        pass
    else:
        return flask.send_from_directory(PATH_DIST, 'index.html')


@app.route("/<path:subpath>")
def subpath(subpath):
    return flask.send_from_directory(PATH_DIST, subpath)


@app.route("/admin/api/fetch_providers")
def api_fake_chart():
    from proxy_providers.wandou import __init__ as wandou

    ret = {
        'ipFetchConsumeChartData': [],
        'ipProviderData': [
            {'cvr': wandou.parse_cvr(), 'name': '豌豆代理'},
        ],
    }

    for i in range(24):
        x, y1 = wandou.parse_one_hour_span(i)
        _, y2 = wandou.parse_one_hour_span(i, 'wandou_fetch')
        ret['ipFetchConsumeChartData'].append(dict(
            x=x,
            y1=y1,
            y2=y2,
        ))

    return flask.jsonify(ret)
