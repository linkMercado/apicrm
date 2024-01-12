# encoding: utf-8
# -*- coding: utf-8 -*-
#

from datetime import date
from apicrm import LOGGER as logger
from apicrm import SUITECRM as SuiteCRM 



def Delete(module:str, entity_data:dict) -> tuple[bool, dict]:
    CRM = SuiteCRM.SuiteCRM(logger)    
    critica = CRM.critica_parametros(module, 'DELETE', entity_data)
    if critica:
        return False, { 'msg': critica }
    d = CRM.DeleteData(module, parametros=entity_data)
    return d, { 'msg': None } if d else { 'msg': 'Erro' }

def Post(module:str, entity_data:dict) -> tuple[bool, dict]:
    CRM = SuiteCRM.SuiteCRM(logger)    
    critica = CRM.critica_parametros(module, 'POST', entity_data)
    if critica:
        return False, { 'msg': critica }
    r = CRM.PostData(module, parametros=entity_data)
    _id = r.get('data',{}).get('saveRecord',{}).get('record',{}).get("_id") if r else None
    if _id:
        return True, {'data': {'id':_id} }
    return False, { 'msg':'ERRO !' }

def Put(module:str, entity_data:dict) -> tuple[bool, dict]:
    CRM = SuiteCRM.SuiteCRM(logger)    
    critica = CRM.critica_parametros(module, 'PUT', entity_data)
    if critica:
        return False, { 'msg': critica }
    r = CRM.PutData(module, parametros=entity_data)
    _id = r.get('data',{}).get('saveRecord',{}).get('record',{}).get("_id") if r else None
    if _id:
        return True, {'data': {'id':_id} }
    return False, { 'msg':'ERRO !' }

def Get(module:str, filtro:dict=None) -> tuple[bool, dict]:
    CRM = SuiteCRM.SuiteCRM(logger)    
    critica = CRM.critica_parametros(module, 'GET', filtro)
    if critica:
        return False, { 'msg': critica }
    return True, { 'data': CRM.GetData(module, filtro=filtro) }
