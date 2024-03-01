# encoding: utf-8
# -*- coding: utf-8 -*-
#

from apicrm import LOGGER as logger


def Delete(CRM, module:str, entity_data:dict) -> tuple[bool, dict]:
    critica = CRM.critica_parametros(module, 'DELETE', entity_data)
    if critica:
        return False, { 'msg': critica }
    d = CRM.DeleteData(module, parametros=entity_data)
    return d, { 'msg': None } if d else { 'msg': 'Erro' }


def Post(CRM, module:str, entity_data:dict) -> tuple[bool, dict]:
    critica = CRM.critica_parametros(module, 'POST', entity_data)
    if critica:
        return False, { 'msg': critica }
    r = CRM.PostData(module, parametros=entity_data)
    _id = r.get('data',{}).get('saveRecord',{}).get('record',{}).get("_id") if r else None
    if _id:
        return True, {'data': {'id':_id} }
    return False, { 'msg':'ERRO !' }


def Put(CRM, module:str, entity_data:dict) -> tuple[bool, dict]:
    critica = CRM.critica_parametros(module, 'PUT', entity_data)
    if critica:
        return False, { 'msg': critica }
    r = CRM.PutData(module, parametros=entity_data)
    _id = r.get('data',{}).get('saveRecord',{}).get('record',{}).get("_id") if r else None
    if _id:
        return True, {'data': {'id':_id} }
    return False, { 'msg':'ERRO !' }


def Get(CRM, module:str, filtro:dict=dict()) -> tuple[bool, dict]:
    critica = CRM.critica_parametros(module, 'GET', filtro)
    if critica:
        return False, { 'msg': critica }
    return True, { 'data': CRM.GetData(module, filtro=filtro) }


def Cria_contato(CRM, parametros):
    return CRM.cria_contato(**parametros)

def Associa_contatos(CRM, conta_id:str, contato_ids:str) -> bool:
    return CRM.AssociateData("accounts", base_record_id=conta_id, relate_module="contacts", relate_record_ids=contato_ids)