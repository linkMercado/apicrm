# encoding: utf-8
# -*- coding: utf-8 -*-

import sys
import config
from lm_packages import Log as logging
from lm_packages import MailBox
from lm_packages.Extras import DefaultConv
from lm_packages import AppControl
from lm_packages    import SuiteCRM

from functools import wraps
from datetime import datetime
from flask import Flask, json, request, Response


LOGGER = logging.setup_custom_logger(**config.LogConfig)
MAILBOX = MailBox.MailBoxLM(LOGGER)
APPCONTROL = AppControl.AppControl(LOGGER, config.APPNAME, port=8904)
SUITECRM = SuiteCRM.SuiteCRM(LOGGER)

LOGGER.info("inicio")

app = Flask(__name__,static_url_path='')
webstart = datetime.now()


def logar(func):
    @wraps(func)
    def inner(*args, **kwargs):
        LOGGER.info(f"w:{request.path} [{request.method}] func:{func.__name__} p:{request.args} b:{request.get_json(silent=True)}")
        resp = func(*args, **kwargs)
        LOGGER.debug(f"w:{request.path} [{request.method}] func:{func.__name__}")
        return resp
    return inner


@app.route('/crm/<module>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@logar
def app_crm(module):
    if request.method == 'GET':
        args = request.args
    else:
        args = request.get_json()

    critica = SUITECRM.critica_parametros(module, request.method, args)
    if critica:
        resp = {'status': 'ERRO', 'msg': critica }
        resp_status = 400
    else:    
        resp_status = 200
        if request.method == 'GET':
            r = SUITECRM.GetData(module, filtro=args)
            if r:
                resp = {'status': 'OK', 'data': r }
            else:
                resp = {'status': 'ERRO', 'msg': 'Informação não encontrada' }
                resp_status = 404
        elif request.method == 'POST':
            r = SUITECRM.PostData(module, parametros=args)
            _id = r.get('data',{}).get('saveRecord',{}).get('record',{}).get("_id") if r else None
            if _id:
                resp = {'status': 'OK', 'data': {'id': _id} }
                resp_status = 201
            else:
                resp = {'status': 'ERRO', 'msg': 'ERRO !' }
                resp_status = 400
        elif request.method == 'PUT':
            r = SUITECRM.PutData(module, parametros=args)
            _id = r.get('data',{}).get('saveRecord',{}).get('record',{}).get("_id") if r else None
            if _id:
                resp = {'status': 'OK', 'data': {'id': _id} }
            else:
                resp = {'status': 'ERRO', 'msg': 'ERRO !' }
                resp_status = 400
        elif request.method == 'DELETE':
            if SUITECRM.DeleteData(module, parametros=args):
                resp = {'status': 'OK'}
            else:
                resp = {'status': 'ERRO', 'msg': 'ERRO !' }
                resp_status = 400
        else:
            resp = {'status': 'ERRO', 'msg': f'método {request.method} não suportado' }
            resp_status = 500
    return Response(json.dumps(resp, default=DefaultConv), mimetype='application/json', status=resp_status) 



@app.route('/_sysinfo', methods=['GET'])
def sys_info():
    return Response(json.dumps(
                        {       "app": APPCONTROL.app_name,
                                "ip": APPCONTROL.ip_address,
                                "Python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                                "alive": datetime.now().strftime("%Y-%m-%d %H: %M: %S"),
                                "since": webstart.strftime("%Y-%m-%d %H: %M: %S"),
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
