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
        args = request.args.to_dict()
    else:
        args = request.get_json()

    status=200
    if procedure == "processa_arquivo_contas":
        msg = ctl_procs.processa_arquivo_contas(**args)
    elif procedure == "processa_arquivo_contratos":
        msg = ctl_procs.processa_arquivo_contratos(**args)
    elif procedure == "processa_arquivo_contatos":
        msg = ctl_procs.processa_arquivo_contatos(**args)
    elif procedure == "deleta_contratos":
        msg = ctl_procs.processa_arquivo_deleta_contratos(**args)
    elif procedure == 'acerta_GC':
         msg = ctl_procs.remove_GC_de_BOAccounts_sem_contrato_ativo()
    else:
        msg = f"Processo {procedure} não encontrado"
        status = 404

    return Response(msg, mimetype='application/json', status=status) 


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


@app.route('/crm/sync/<module>', methods=[ 'GET', 'POST', 'PUT'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
@logar
def app_sync_module(module:str):
    resp_status = None
    msg = None

    if request.method == 'GET':
        args = request.args.to_dict()
    elif request.method in ['POST', 'PUT']:
        args = request.get_json()
    else:
        args = None
        resp_status = 400
        msg = "Método não implementado"

    if args:
        if request.method in ['GET']:
            resp_status = 200
            mimetype = 'application/json'
            if module in ['account', 'bu']:
                resp = ctl_procs.get_sync_bu(args=args)
            elif module in ['boconta', 'boaccount']:
                resp = ctl_procs.get_sync_boconta(args=args)
            elif module in ['contract', 'contrato']:
                resp = ctl_procs.get_sync_contract(args=args)
            elif module in ['contact', 'contato']:
                resp = ctl_procs.get_sync_contact(args=args)
            elif module in ['task', 'tarefa']:
                resp = ctl_procs.get_sync_task(args=args)
            elif module in ['project', 'projeto']:
                resp = ctl_procs.get_sync_project(args=args)
            else:
                msg = "Módulo desconhecido"   
            if not msg:
                if resp:
                    msg = json.dumps(resp, default=DefaultConv)
                else:
                    resp_status = 404
                    mimetype = 'application/text'
                    msg = "Nenhum registro encontrado"
        elif request.method in ['POST', 'PUT']:
            resp_status = 200
            mimetype = 'application/text'
            if module in ['account', 'bu']:
                msg = ctl_procs.sync_bu(account_data=args)
            elif module in ['boconta', 'boaccount']:
                resp = ctl_procs.sync_boconta(boaccount_data=args)
            elif module in ['contract', 'contrato']:
                msg = ctl_procs.sync_contract(contract_data=args)
            elif module in ['contact', 'contato']:
                msg = ctl_procs.sync_contact(contact_data=args)
            elif module in ['task', 'tarefa']:
                msg = ctl_procs.sync_task(task_data=args)
            elif module in ['project', 'projeto']:
                msg = ctl_procs.sync_project(project_data=args)
            else:
                resp_status = 404
                msg = "Módulo desconhecido"   

    LOGGER.debug(f"sync_{module}, s:{resp_status} m:{msg}")
    return Response(msg, mimetype=mimetype, status=resp_status) 

@app.route('/crm/bus_candidatas', methods=['GET'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
@logar
def app_busca_bus_candidatas():
    resp = ctl_procs.bus_candidatas(lead_data=request.args.to_dict())
    return Response(json.dumps(resp, default=DefaultConv), mimetype='application/json', status=200) 


@app.route('/crm/sync/xaccount', methods=[ 'GET', 'POST', 'PUT'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
@logar
def app_sync_account():
    if request.method == 'GET':
        args = request.args.to_dict()
    else:
        args = request.get_json()
    buids = args.get('buid')
    accountid = args.get('accountid')
    userid = args.get('userid')

    resp_status = 200
    if buids or accountid:
        if buids:
            accountid = None
            resp = {'status': 'ERRO', 'msg': 'Account_id não encontrado na Base' }
            resp_status = 400

            accids = dal_lm.GetAccountsIDs([buids,])
            if accids:
                if len(accids) == 1:
                    accountid = accids[0].get('account_id')
                elif len(accids) > 1:
                    resp = {'status': 'ERRO', 'msg': 'Mais de um account_id informado, verifique !' }
                    resp_status = 400
        if accountid:                
            msg, buids = ctl_procs.sync_BO2CRM_Account(account_id=accountid, userid=userid)
            resp = {'status': 'OK' if msg else 'ERRO', 'msg' : msg, 'buids' : buids }
            resp_status = 200 if msg else 400
    else:
        resp = {'status': 'ERRO', 'msg': 'BU id não informado [buid]' }
        resp_status = 400
    LOGGER.debug(f"s:{resp_status} m:{resp}")
    return Response(json.dumps(resp, default=DefaultConv), mimetype='application/json', status=resp_status) 


@app.route('/crm/sync/xcontract', methods=['POST', 'PUT'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
@logar
def app_sync_contract():
    if request.method == 'GET':
        args = request.args.to_dict()
        args - None
        resp_status = 400
        msg = "Metodo não implementado"
    elif request.method in ['POST', 'PUT']:
        args = request.get_json()
    else:
        args = None
        resp_status = 400
        msg = "Método não implementado"
    if args:
        resp_status = 200
        msg = ctl_procs.sync_contract(contract_data=args)
    else:
        resp_status = 400
        msg = 'Erro: chamada sem body'
    LOGGER.debug(f"s:{resp_status} m:{msg}")
    return Response(msg, mimetype='application/text', status=resp_status) 


@app.route('/crm/notification', methods=['POST'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
@logar
def app_notification():
    if request.method == 'GET':
        args = request.args.to_dict()
    else:
        args = request.get_json()
    idcliente = args.get('idcliente')
    buid = args.get('buid')
    name = args.get('nome')    
    mensagem = args.get('mensagem')    
    assigned_user_name = args.get('assigned')
    crm_account_id = None
    crm_gerente_relacionamento = None
    CRM = SuiteCRM.SuiteCRM(LOGGER) 
    if idcliente:
        crm_account = dal_crm.Account_Get(CRM,id_cliente_c=idcliente)
        if crm_account and len(crm_account) == 1:
            crm_account_id = crm_account[0].get('id')
            crm_gerente_relacionamento = crm_account[0].get('users_accounts_1users_ida')
    elif buid:
        crm_account = dal_crm.Account_Get(CRM, bu_id_c=buid)
        if crm_account and len(crm_account) == 1:
            crm_account_id = crm_account[0].get('id')
    # se exiate no CRM -> ticket else task
    if crm_account_id:                
        _resp = CRM.cria_ticket(account_id=crm_account_id,
                                name=name,
                                description=mensagem,
                                type="Register",
                                priority="P2",
                                assigned_user_id=crm_gerente_relacionamento,
                                date_entered="agora"
        )
        resp = {'status': 'OK' if _resp else 'ERRO'}
        resp_status = 200 if _resp else 400
    else:
        _resp = CRM.cria_task(  name=name,
                                description=mensagem,
                                assigned_user_id= "nome do gerente de relacionamento",
                                date_entered="agora",
                                status="Completed" "Not Started",
                                priority="Medium",
        )
        resp = {'status': 'OK' if _resp else 'ERRO'}
        resp_status = 200 if _resp else 400

    LOGGER.debug(f"s:{resp_status} m:{resp}")
    return Response(json.dumps(resp, default=DefaultConv), mimetype='application/json', status=resp_status) 


@app.route('/crm/<module>', methods=['GET']) # ['GET', 'POST', 'PUT', 'DELETE'])
@logar
def app_crm(module):
    if request.method == 'GET':
        args = request.args.to_dict()
        if not args:
            args = request.get_json()
    else:
        args = request.get_json()

    resp_status = 200
    if request.method == 'GET':
        s, d = ctl_procs.Get(module, filtro=args)
        if s:
            resp = {'status': 'OK', 'data': d.get('data') }
        else:
            resp = {'status': 'ERRO', 'msg': d.get('msg') }
    elif request.method == 'POST':
        s, d = ctl_procs.Post(module, entity_data=args)
        if s:
            resp = {'status': 'OK', 'data': d.get('data') }
        else:
            resp = {'status': 'ERRO', 'msg': d.get('msg') }
    elif request.method == 'PUT':
        s, d = ctl_procs.Put(module, entity_data=args)
        if s:
            resp = {'status': 'OK', 'data': d.get('data') }
        else:
            resp = {'status': 'ERRO', 'msg': d.get('msg') }
    elif request.method == 'DELETE':
        s, d = ctl_procs.Delete(module, entity_data=args)
        if s:
            resp = {'status': 'OK'}
        else:
            resp = {'status': 'ERRO', 'msg': d.get('msg') }
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
