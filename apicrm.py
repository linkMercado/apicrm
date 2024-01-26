# encoding: utf-8
# -*- coding: utf-8 -*-

import sys
import config
from lm_packages import Log as logging
from lm_packages import MailBox
from lm_packages import MySQLPool as MySQLPool
from lm_packages.Extras import DefaultConv
from lm_packages import AppControl
from lm_packages import SuiteCRM

from functools import wraps
from datetime import datetime
from flask import Flask, json, request, Response

from functools import update_wrapper

from flask_cors import CORS, cross_origin

LOGGER = logging.setup_custom_logger(**config.LogConfig)
MAILBOX = MailBox.MailBoxLM(LOGGER)
MYSQLPOOL = MySQLPool.MySQLDBPool(LOGGER, **config.DbConfig)
APPCONTROL = AppControl.AppControl(LOGGER, config.APPNAME, port=8904)
SUITECRM = SuiteCRM

from controllers import ctl_sync

from dal import dal_crm
from dal import dal_lm

LOGGER.info("inicio")

app = Flask(__name__,static_url_path='')
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy   dog'
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app, resources={r"/crm/sync/account": {"origins": "*"}})

webstart = datetime.now()


def logar(func):
    @wraps(func)
    def inner(*args, **kwargs):
        LOGGER.info(f"w:{request.path} [{request.method}] func:{func.__name__} p:{request.args} b:{request.get_json(silent=True)}")
        resp = func(*args, **kwargs)
        LOGGER.debug(f"w:{request.path} [{request.method}] func:{func.__name__}")
        return resp
    return inner



def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


@app.route('/crm/<module>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@logar
def app_crm(module):
    if request.method == 'GET':
        args = request.args
    else:
        args = request.get_json()

    resp_status = 200
    if request.method == 'GET':
        s, d = dal_crm.Get(module, filtro=args)
        if s:
            resp = {'status': 'OK', 'data': d.get('data') }
        else:
            resp = {'status': 'ERRO', 'data': d.get('msg') }
    elif request.method == 'POST':
        s, d = dal_crm.Post(module, entity_data=args)
        if s:
            resp = {'status': 'OK', 'data': d.get('data') }
        else:
            resp = {'status': 'ERRO', 'msg': d.get('msg') }
    elif request.method == 'PUT':
        s, d = dal_crm.Put(module, entity_data=args)
        if s:
            resp = {'status': 'OK', 'data': d.get('data') }
        else:
            resp = {'status': 'ERRO', 'msg': d.get('msg') }
    elif request.method == 'DELETE':
        s, d = dal_crm.Delete(module, entity_data=args)
        if s:
            resp = {'status': 'OK'}
        else:
            resp = {'status': 'ERRO', 'msg': d.get('msg') }
    else:
        resp = {'status': 'ERRO', 'msg': f'método {request.method} não suportado' }
        resp_status = 500
    return Response(json.dumps(resp, default=DefaultConv), mimetype='application/json', status=resp_status) 


@app.after_request
def after_request(response: Response) -> Response:
    response.access_control_allow_credentials = True
    return response


@app.route('/crm/sync/account', methods=[ 'GET', 'POST', 'PUT'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
@logar
def app_sync():
    if request.method == 'GET':
        args = request.args
    else:
        args = request.get_json()
    buids = args.get('buids')
    userid = args.get('userid')
    msg = []
    resp_status = 200
    if buids:
        for buid in buids.split(','):
            r = ctl_sync.sync_account(buid, userid)
            msg.append(f"{buid} {'não' if not r else ''} sincronizada")
        resp = {'status': 'OK' if r else 'ERRO', 'msg' : msg }
        resp_status = 200
    else:
        resp = {'status': 'ERRO', 'msg': 'BU id não informado [buid]' }
        resp_status = 400
    return Response(json.dumps(resp, default=DefaultConv), mimetype='application/json', status=resp_status) 


@app.route('/_sysinfo', methods=['GET'])
def sys_info():
    return Response(json.dumps(
                        {       "app": APPCONTROL.app_name,
                                "ip": APPCONTROL.ip_address,
                                "Python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                                "alive": datetime.now().strftime("%Y-%m-%d %H: %M: %S"),
                                "since": webstart.strftime("%Y-%m-%d %H: %M: %S"),
                                'LM': dal_lm.getPoolInfo(), 
                                # "CRM": SUITECRM.Status()
                        }, default=DefaultConv
                    ), 
                    mimetype='application/json'
    ) 


@app.route('/crm/_appinfo', methods=['GET'])
def app_info():
    return Response(json.dumps(APPCONTROL.AppInfo(), default=DefaultConv), mimetype='application/json') 


@app.route("/")
def app_alive():
    return Response(status=204)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
