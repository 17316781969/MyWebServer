import flask

from MyWebServer.v2 import app
from .v2 import WorkerManager


###
@app.before_request
def worker_before_request():
    if flask.request.path.startswith('/worker'):
        flask.request.cpu_count = int(flask.request.headers.get('cpu_count', default=0))
        flask.request.host_name = flask.request.headers.get('host_name', default='unknown')
        flask.request.localhost = flask.request.headers.get('localhost', default='unknown')
        flask.request.length_browsers_full = int(flask.request.headers.get('length_browsers_full', default=0))
        flask.request.length_browsers_now = int(flask.request.headers.get('length_chromedrivers', default=0))

        WorkerManager.alive(
            hostname=flask.request.host_name,
            **dict(
                cpu_count=flask.request.cpu_count,
                ip=flask.request.remote_addr,
                # length_browsers_full=flask.request.length_browsers_full,
                length_browsers_now=flask.request.length_browsers_now,
            )
        )


@app.route("/worker/breath")
def worker_breath():
    ret_d = dict(ret=0, msg="")

    # 将请求写进日志
    app.logger.info(
        f"Worker\n\tCPUCount: \t{flask.request.cpu_count}"
        f"\n\tHostName: \t{flask.request.host_name}"
        f"\n\tPath: \t{flask.request.path}"
        f"\n\tLengthBrowsersFull: \t{flask.request.length_browsers_full}"
    )

    # 判断请求 CPU 参数
    j = WorkerManager.breath(flask.request.host_name)
    length_browsers_full: str = j.get('length_browsers_full')
    if length_browsers_full:
        try:
            length_browsers_full = int(length_browsers_full)
        except:
            app.logger.info('worker_breath "length_browsers_full" 值错误')
            flask.abort(500)
    else:
        length_browsers_full = flask.request.cpu_count
    ret_d['length_browsers_full'] = length_browsers_full

    return flask.jsonify(ret_d)


@app.route("/set/threads/<target>/<surplus>")
def worker_set_num_threads(target=0, surplus=0):
    ret = dict(ret=0, msg="")
    if target == 0:
        ret['target']=0
        return flask.jsonify(ret)
    j = WorkerManager.set_num_threads(target, surplus)
    length_browsers_full: str = j.get('length_browsers_full')
    if length_browsers_full:
        ret['length_browsers_full'] = length_browsers_full
    return flask.jsonify(ret)