"""

全面基于 MongoDB

"""

import os

import flask
import pymongo
from flask_pymongo import PyMongo

__name__ = 'WebServer'
__author__ = 'Chang.'

from utils import logger_web_server, Docker

app = flask.Flask(__name__)
app.debug = bool(os.environ.get("DEBUG"))
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
app.config['JSON_AS_ASCII'] = False
# app.config["MONGO_URI"] = f"mongodb://192.168.2.100:27017/fake_flow"
app.config["MONGO_URI"] = f"mongodb://{Docker.gateway if Docker else '127.0.0.1'}:27017/fake_flow"

app.logger = logger_web_server

mongo = PyMongo(app, maxPoolSize=200, waitQueueMultiple=20)


@app.route('/')
def help():
    return '</br>'.join("""
# WebServer 2.*

公司内部使用

目前支持路径

## proxy

* /proxy/
* /proxy/paid/wandou

## faker

* /faker/pc
* /faker/wechat
* /faker/wechat/ios
""".splitlines(keepends=True))


@app.errorhandler(404)
def not_found(e):
    app.logger.exception('error 404: %s', e)
    return flask.jsonify({
        'reason': 'resource not found',
        'status_code': 404,
        'ret': -1,
    })


@app.errorhandler(500)
def not_found(e):
    app.logger.exception('error 500: %s', e)
    return flask.jsonify({
        'reason': 'internal server error',
        'status_code': 500,
        'ret': -1,
    })


import MyWebServer.faker
import MyWebServer.proxy
import MyWebServer.mission
import MyWebServer.settings
import MyWebServer.worker

mongo.db.set_profiling_level(level=pymongo.SLOW_ONLY, slow_ms=100)
