import flask

from MyWebServer.v2 import app

from fake_identity.HereNoSpider import HereNoSpider
from fake_identity.HereNowWechat import HereNowWechat


@app.route("/faker/pc")
def fake_pc():
    return flask.jsonify({
        'ret': 0,
        'user-agent': HereNoSpider.pc
    })


@app.route("/faker/wechat")
def fake_wechat():
    return flask.jsonify({
        'ret': 0,
        'user-agent': HereNowWechat.random
    })


@app.route("/faker/wechat/ios")
def fake_wechat_ios():
    return flask.jsonify({
        'ret': 0,
        'user-agent': HereNowWechat.iphone
    })
