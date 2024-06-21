# encoding: utf-8
# -*- coding: utf-8 -*-
#

import re
from apicrm import LOGGER as logger
from apicrm import SUITECRM as SuiteCRM

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
    _, r = CRM.PostData(module, parametros=entity_data)
    _id = r.get("id") if r else None
    if _id:
        return True, {'data': {'id':_id} }
    return False, { 'msg':'ERRO !' }


def Put(CRM, module:str, entity_data:dict) -> tuple[bool, dict]:
    critica = CRM.critica_parametros(module, 'PUT', entity_data)
    if critica:
        return False, { 'msg': critica }
    _, r = CRM.PutData(module, parametros=entity_data)
    _id = r.get("id") if r else None
    if _id:
        return True, {'data': {'id':_id} }
    return False, { 'msg':'ERRO !' }


def Get(CRM, module:str, filtro:dict=dict()) -> tuple[bool, dict]:
    critica = CRM.critica_parametros(module, 'GET', filtro)
    if critica:
        return False, { 'msg': critica }
    return True, { 'data': CRM.GetData(module, filtro=filtro) }


def Account_Get(CRM, id:str=None, account_id:str=None, buid:str=None, id_cliente:str=None, status:str=None) -> dict:
    filtro = dict()
    if id:
        filtro['id'] = id
    if account_id:
        filtro['id_conta_lm_c'] = str(account_id)
    if id_cliente:
        filtro['id_cliente_c'] = str(id_cliente)
    if buid:
        filtro['bu_id_c'] = str(buid)
    if status:
        filtro['status_c'] = status
    resp = CRM.GetData("accounts", filtro=filtro)
    resposta = list()
    for r in resp:
        if id and r['id'] == id:
            return resp
        elif account_id and r['id_conta_lm_c'] != str(account_id):
            continue
        elif id_cliente and r['id_cliente_c'] != str(id_cliente):
            continue
        elif buid and r['bu_id_c'] != str(buid):
            continue
        elif status and r['status_c'] != str(status):
            continue
        resposta.append(r)
    return resposta

def Account_Create(CRM, account_data:dict) -> tuple[str,dict]:
    if account_data:
        return CRM.PostData("accounts", parametros=account_data)
    else:
        return 'sem dados para cadastrar', None


def Account_Update(CRM, account_data:dict) -> tuple[str,dict]:
    if account_data:
        return CRM.PutData("accounts", parametros=account_data)
    else:
        return "Sem informação", None

def Account_RemoveGrupoSeguranca(CRM, account_id:str, gerente_relacionamento_name:str):
    if gerente_relacionamento_name:
        # pega o id do Grupo de Segurança do gerente
        grupo = CRM.getSecurityGroup(f"Gerente {gerente_relacionamento_name}")
        #e desassocia
        _ = CRM.Desassocia(base_module="accounts", base_record_id=account_id, relate_module="security-groups", relate_record_ids=grupo['id'])
        print(_)

def Account_Delete(CRM, crm_id:str) -> dict:
    if crm_id:
        return CRM.DeleteData("accounts", parametros={'id':crm_id})
    else:
        return False


def User_Get(CRM, id:str=None, username:str=None, email:str=None) -> dict:
    return CRM.getColaborador(id=id, username=username, email=email)


def Contact_Get(CRM, id:str=None, name:str=None, email:str=None, document:str=None, phone:str=None, mobile_phone:str=None, whatsapp:str=None) -> dict:
    filtro = dict()
    if id:
        filtro['id'] = id
    if name:
        filtro['name'] = name
        __name = re.sub('[^a-zA-Z0-9]', '', name)
    else:
        __name = None
    if email:
        filtro['email'] = email
        __email = email
    else:
        __email = None
    if document:
        filtro['cpf_c'] = document
        __document = re.sub('[^0-9]', '', document)
    else:
        __document = None
    if phone:
        filtro['phone_work'] = SuiteCRM.format_phone(phone)
        __phone = SuiteCRM.format_phone(phone)
    else:
        __phone = None
    if mobile_phone:
        filtro['phone_mobile'] = mobile_phone
        __mobile_phone = SuiteCRM.format_phone(mobile_phone, internacional=True)
    else:
        __mobile_phone = None
    if whatsapp:
        filtro['phone_fax'] = whatsapp
        __whatsapp = SuiteCRM.format_phone(whatsapp, internacional=True)
    else:
        __whatsapp = None
    
    if filtro:        
        crm_contatos = CRM.GetData("contacts", filtro=filtro)
    
        # se retornou mais de um, qual dos contatos ?
        _crm_contato = None
        if crm_contatos and len(crm_contatos) == 1:
            _crm_contato = crm_contatos[0]
        else:
            nota_maxima = 0
            for crm_contato in crm_contatos if crm_contatos else []:
                nota = 0
                nota += 1 if __name and re.sub('[^a-zA-Z0-9]', '', crm_contato.get('name') if crm_contato.get('name') else '') == __name else 0
                nota += 1 if __email and crm_contato.get('email') == __email else 0
                nota += 1 if __document and re.sub('[^0-9]', '', crm_contato.get('document') if crm_contato.get('document') else '') == __document else 0
                nota += 1 if __phone and SuiteCRM.format_phone(crm_contato.get('phone'), internacional=True) == __phone else 0
                nota += 1 if __mobile_phone and SuiteCRM.format_phone(crm_contato.get('mobile_phone'), internacional=True) == __mobile_phone else 0
                nota += 1 if __whatsapp and SuiteCRM.format_phone(crm_contato.get('phone_fax'), internacional=True) == __whatsapp else 0
                if nota > nota_maxima:
                    nota_maxima = nota
                    _crm_contato = crm_contato
        return _crm_contato


    else:
        return None


def Contact_Create(CRM, contact_data:dict) -> tuple[str,dict]:
    if contact_data:
        return CRM.PostData("contacts", parametros=contact_data)
    else:
        return 'Sem informação', None


def Contact_Update(CRM, contact_data:dict) -> tuple[str,dict]:
    if contact_data:
        return CRM.PutData("contacts", parametros=contact_data)
    else:
        return "Sem Informação", None
    

def Contract_Get(CRM, id:str=None, name:str=None) -> dict:
    filtro = dict()
    if id:
        filtro['id'] = id
    if name:
        filtro['name'] = name
    if filtro:        
        return CRM.GetData("AOS_Contracts", filtro=filtro)
    else:
        return None


def Contract_Create(CRM, contract_data:dict) -> tuple[str,dict]:
    if contract_data:
        return CRM.PostData("AOS_Contracts", parametros=contract_data)
    else:
        return 'Sem informação', None
    

def Contract_Update(CRM, contract_data:dict) -> tuple[str,dict]:
    if contract_data:
        return CRM.PutData("AOS_Contracts", parametros=contract_data)
    else:
        return "Sem Informação", None


def Cria_contato(CRM, parametros) -> tuple[str,dict]:
    return CRM.cria_contato(**parametros)


def Ticket_Create(CRM, ticket_data:dict) -> tuple[str,dict]:
    if ticket_data:
        return CRM.PostData("tickets", parametros=ticket_data)
    else:
        return "Sem informação", None


def ContaBO_Update(CRM, contaBO_data:dict) -> tuple[str,dict]:
    if contaBO_data:
        return CRM.PutData("GCR_ContaBackoffice", parametros=contaBO_data)
    else:
        return "Sem informação", None

def Associa_contatos(CRM, crm_account_id:str, crm_contact_ids:str) -> bool:
    return CRM.AssociateData("accounts", base_record_id=crm_account_id, relate_module="contacts", relate_record_ids=crm_contact_ids)


def Associa_contratos(CRM, crm_account_id:str, crm_contract_ids:str) -> bool:
    return CRM.AssociateData("accounts", base_record_id=crm_account_id, relate_module="contracts", relate_record_ids=crm_contract_ids)
