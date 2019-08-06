import flask

from MyWebServer.v2 import app
from .v2 import SettingsManager


@app.route('/setting/get/<string:name>')
def setting_get(name=None):
    if name:
        ret = SettingsManager.get(name)
        return flask.jsonify(dict(
            ret=0,
            data=ret
        ))

    return flask.jsonify(dict(
        ret=-1,
    ))


@app.route('/setting/set/<string:name>', methods=['POST'])
def setting_set(name=None):
    data = flask.request.json
    if not data:
        data = flask.request.values
    if not name or not data or 'value' not in data:
        return flask.jsonify(dict(
            ret=-1,
        ))

    value = data['value']

    return flask.jsonify(dict(
        ret=0,
        msg=SettingsManager.set(name, value)
    ))
