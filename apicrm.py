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
from flask import Flask, json, request, Response, make_response 
from flask_cors import CORS, cross_origin


LOGGER = logging.setup_custom_logger(**config.LogConfig)
MAILBOX = MailBox.MailBoxLM(LOGGER)
MYSQLPOOL = MySQLPool.MySQLDBPool(LOGGER, **config.DbConfig)
APPCONTROL = AppControl.AppControl(LOGGER, config.APPNAME, port=8904)
SUITECRM = SuiteCRM

from controllers import ctl_procs

from dal import dal_crm
from dal import dal_lm

LOGGER.info("inicio")

app = Flask(__name__,static_url_path='')
cors = CORS(app, resources={r"/crm/*": {"origins": "*"}})

webstart = datetime.now()


def logar(func):
    @wraps(func)
    def inner(*args, **kwargs):
        LOGGER.info(f"w:{request.path} [{request.method}] func:{func.__name__} p:{request.args} b:{request.get_json(silent=True)}")
        resp = func(*args, **kwargs)
        LOGGER.debug(f"w:{request.path} [{request.method}] func:{func.__name__}")
        return resp
    return inner




@app.route('/crm/procedure/<procedure>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@logar
def app_procedures(procedure):
    if request.method == 'GET':
        args = request.args
    else:
        args = request.get_json()
    if procedure == "cria_notificacao":
        try:
            msg = ctl_procs.cria_notificacao(**args)
        except Exception as e:
            msg = f"{e}"
    return Response(msg, mimetype='application/json', status=200) 



@app.route('/crm/<module>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@logar
def app_crm(module):
    if request.method == 'GET':
        args = request.args
    else:
        args = request.get_json()
    
    CRM = SuiteCRM.SuiteCRM(LOGGER) 
    resp_status = 200
    if request.method == 'GET':
        s, d = dal_crm.Get(CRM, module, filtro=args)
        if s:
            resp = {'status': 'OK', 'data': d.get('data') }
        else:
            resp = {'status': 'ERRO', 'msg': d.get('msg') }
    elif request.method == 'POST':
        s, d = dal_crm.Post(CRM, module, entity_data=args)
        if s:
            resp = {'status': 'OK', 'data': d.get('data') }
        else:
            resp = {'status': 'ERRO', 'msg': d.get('msg') }
    elif request.method == 'PUT':
        s, d = dal_crm.Put(CRM, module, entity_data=args)
        if s:
            resp = {'status': 'OK', 'data': d.get('data') }
        else:
            resp = {'status': 'ERRO', 'msg': d.get('msg') }
    elif request.method == 'DELETE':
        s, d = dal_crm.Delete(CRM, module, entity_data=args)
        if s:
            resp = {'status': 'OK'}
        else:
            resp = {'status': 'ERRO', 'msg': d.get('msg') }
    else:
        resp = {'status': 'ERRO', 'msg': f'método {request.method} não suportado' }
        resp_status = 500
    return Response(json.dumps(resp, default=DefaultConv), mimetype='application/json', status=resp_status) 


@app.after_request
def after_request_func(response: Response) -> Response:
    origin = request.headers.get('Origin')
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Headers', 'x-csrf-token')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE') # PATCH
        if origin:
            response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        if origin:
            response.headers.add('Access-Control-Allow-Origin', origin)

    return response


@app.route('/crm/sync/account', methods=[ 'GET', 'POST', 'PUT'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
@logar
def app_sync():
    if request.method == 'GET':
        args = request.args
    else:
        args = request.get_json()
    buids = str(args.get('buid'))
    accountid = str(args.get('accountid'))
    userid = args.get('userid')
    msg = []
    resp_status = 200
    if buids or accountid:
        if buids:
            accids = dal_lm.GetAccountsIDs([buids,])
            if accids and len(accids) == 1:
                accountid = accids[0].get('account_id')
            else:
                accountid = None
        if accountid:                
            _resp, buids = ctl_procs.sync_BO2CRM_Account(account_id=accountid, userid=userid)
            resp = {'status': 'OK' if _resp else 'ERRO', 'msg' : msg, 'buids' : buids }
            resp_status = 200 if _resp else 400
        else:
            resp = {'status': 'ERRO', 'msg': 'Account_id id não encontrado na Base' }
            resp_status = 400
    else:
        resp = {'status': 'ERRO', 'msg': 'BU id não informado [buid]' }
        resp_status = 400
    LOGGER.debug(f"s:{resp_status} m:{resp}")
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
