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


def Account_Get(CRM, id:str, account_id:str=None) -> dict:
    filtro = dict()
    if id:
        filtro['id'] = id
    if account_id:
        filtro['id_conta_lm_c'] = account_id
    return CRM.GetData("accounts", filtro=filtro)


def Account_Create(CRM, account_data:dict) -> dict:
    if account_data:
        r = CRM.PostData("accounts", parametros=account_data)
        # id = r.get('data',{}).get('saveRecord',{}).get('record',{}).get("_id") if r else None        
        return r.get('data',{}).get('saveRecord',{}).get('record',{}).get('attributes') if r else None
    else:
        return None


def Account_Update(CRM, account_data:dict) -> dict:
    if account_data:
        r = CRM.PutData("accounts", parametros=account_data)
        id = r.get('data',{}).get('saveRecord',{}).get('record',{}).get("_id") if r else None        
        return True if id else False
    else:
        return False


def User_Get(CRM, id:str=None, email:str=None) -> dict:
    filtro = dict()
    if id:
        filtro['id'] = id
    if email:
        filtro['email'] = email
    if filtro:        
        return CRM.GetData("users", filtro=filtro)
    else:
        return None


def Contact_Get(CRM, id:str=None, name:str=None, email:str=None, document:str=None, phone:str=None, mobile_phone:str=None) -> dict:
    filtro = dict()
    if id:
        filtro['id'] = id
    if id:
        filtro['name'] = name
    if email:
        filtro['email'] = email
    if document:
        filtro['cpf_c'] = document
    if phone:
        filtro['phone_work'] = phone
    if mobile_phone:
        filtro['phone_mobile'] = mobile_phone
    if filtro:        
        return CRM.GetData("contacts", filtro=filtro)
    else:
        return None


def Contact_Create(CRM, contact_data:dict) -> dict:
    if contact_data:
        r = CRM.PostData("contacts", parametros=contact_data)
        return r
    else:
        return None


def Cria_contato(CRM, parametros):
    return CRM.cria_contato(**parametros)


def Associa_contatos(CRM, crm_account_id:str, crm_contact_ids:str) -> bool:
    return CRM.AssociateData("accounts", base_record_id=crm_account_id, relate_module="contacts", relate_record_ids=crm_contact_ids)