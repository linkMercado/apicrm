# encoding: utf-8
# -*- coding: utf-8 -*-
#

import re
from apicrm import LOGGER as logger
from apicrm import SUITECRM as SuiteCRM

def DeleteObject(CRM:SuiteCRM.SuiteCRM, module:str, entity_data:dict) -> tuple[bool, dict]:
    critica = CRM.critica_parametros(module, 'DELETE', entity_data)
    if critica:
        return False, { 'msg': critica }
    d = CRM.DeleteData(module, parametros=entity_data)
    return d, { 'msg': None } if d else { 'msg': 'Erro' }


def PostObject(CRM:SuiteCRM.SuiteCRM, module:str, entity_data:dict) -> tuple[bool, dict]:
    critica = CRM.critica_parametros(module, 'POST', entity_data)
    if critica:
        return False, { 'msg': critica }
    _, r = CRM.PostData(module, parametros=entity_data)
    _id = r.get("id") if r else None
    if _id:
        return True, {'data': {'id':_id} }
    return False, { 'msg':'ERRO !' }


def PutObject(CRM:SuiteCRM.SuiteCRM, module:str, entity_data:dict) -> tuple[bool, dict]:
    critica = CRM.critica_parametros(module, 'PUT', entity_data)
    if critica:
        return False, { 'msg': critica }
    _, r = CRM.PutData(module, parametros=entity_data)
    _id = r.get("id") if r else None
    if _id:
        return True, {'data': {'id':_id} }
    return False, { 'msg':'ERRO !' }


def GetObject(CRM:SuiteCRM.SuiteCRM, module:str, filtro:dict=dict()) -> tuple[bool, dict]:
    critica = CRM.critica_parametros(module, 'GET', filtro)
    if critica:
        return False, { 'msg': critica }
    return True, { 'data': CRM.GetData(module, filtro=filtro) }


def Accounts(CRM) -> list[dict]:
    return CRM.GetData("accounts", filtro={})
    

def Account_Get(CRM:SuiteCRM.SuiteCRM, filtro:dict) -> list[dict]:
    if filtro:
        return CRM.GetData("accounts", filtro=filtro)
    else:
        return list()


def Account_Create(CRM:SuiteCRM.SuiteCRM, account_data:dict) -> tuple[str,dict]:
    if account_data:
        s, d = CRM.PostData("accounts", parametros=account_data)
        if s:
            logger.critical(f"Account não foi criado. erro:{s}, dados:{account_data}")
        else:
            logger.info(f"Account foi criado. dados:{account_data}")
        return s, d
    else:
        return 'sem dados para cadastrar', None


def Account_Update(CRM:SuiteCRM.SuiteCRM, account_data:dict) -> tuple[str,dict]:
    if account_data:
        s, d = CRM.PutData("accounts", parametros=account_data)
        if s:
            logger.critical(f"Account não foi atualizado. erro:{s}, dados:{account_data}")
        else:
            logger.info(f"Account foi atualizado. dados:{account_data}")
        return s, d
    else:
        return "Sem informação", None


def Account_RemoveGrupoSeguranca(CRM:SuiteCRM.SuiteCRM, account_id:str, grupos:str) -> None:
    if grupos:
        for sec_g in grupos.split(','):
            _ = CRM.Desassocia(base_module="accounts", base_record_id=account_id, relate_module="security-groups", relate_record_id=sec_g)


def Account_Delete(CRM:SuiteCRM.SuiteCRM, crm_id:str) -> bool:
    if crm_id:
        logger.info(f"Account {crm_id} foi deletada do CRM.")
        s = CRM.DeleteData("accounts", parametros={'id':crm_id})
        if not s:
            logger.critical(f"Account não foi deletado. id=:{crm_id}")
        else:
            logger.info(f"Account foi deletado. id=:{crm_id}")
        return s
    else:
        logger.critical(f"Account {crm_id} não foi deletada do CRM.")
        return False


def Account_getContacts(CRM:SuiteCRM.SuiteCRM, account_id:str) -> list[dict]:
    contacts = CRM.GetSubPanelData(parentModule="accounts", parentId=account_id, module="contacts", subpanel="contacts")
    if contacts and len(contacts) > 0:
        return contacts
    else:
        return None


def User_Get(CRM:SuiteCRM.SuiteCRM, id:str=None, username:str=None, email:str=None) -> list[dict]:
    if username:
        if '.' in username:
            filtro = {"user_name": username}
        elif username == username.upper():
            filtro = {"usercorp_c": username}
        else:
            filtro = {"name": username}
    if email:
        filtro = {"userlm_c": email}
    if id:
        filtro = {"id": id}

    usuarios = CRM.GetData("users", filtro)
    if len(usuarios) > 0:
        return usuarios
    else:
        return None


def Contact_Get(CRM:SuiteCRM.SuiteCRM, filtro:dict) -> list[dict]:
    if filtro:
        return CRM.GetData("contacts", filtro=filtro)
    else:
        return []


def Contact_Create(CRM:SuiteCRM.SuiteCRM, contact_data:dict) -> tuple[str,dict]:
    if contact_data:
        s, d = CRM.PostData("contacts", parametros=contact_data)
        if s:
            logger.critical(f"Contato não foi criado. erro:{s}, dados:{contact_data}")
        else:
            logger.info(f"Contato não criado. dados:{contact_data}")
        return s, d
    else:
        return 'Sem informação', None


def Contact_Update(CRM:SuiteCRM.SuiteCRM, contact_data:dict) -> tuple[str,dict]:
    if contact_data:
        s, d = CRM.PutData("contacts", parametros=contact_data)
        if s:
            logger.critical(f"Contato não foi atualizado. erro:{s}, dados:{contact_data}")
        else:
            logger.info(f"Contato foi atualizado. dados:{contact_data}")
        return s, d
    else:
        return "Sem Informação", None


def Contact_Delete(CRM:SuiteCRM.SuiteCRM, crm_id:str) -> bool:
    if crm_id:
        s = CRM.DeleteData("contacts", parametros={'id':crm_id})
        if not s:
            logger.critical(f"Contato não foi deletado. id:{crm_id}")
        else:
            logger.info(f"Contato foi deletado. id:{crm_id}")
        return s
    else:
        return False


def Contact_AssociaAccounts(CRM:SuiteCRM.SuiteCRM, crm_contact_id:str, crm_account_id:str) -> bool:
    return CRM.AssociateData("contacts", base_record_id=crm_contact_id, relate_module="accounts", relate_record_ids=crm_account_id)


def Contract_Get(CRM:SuiteCRM.SuiteCRM, filtro:dict) -> list[dict]:
    if filtro:       
        return CRM.GetData("AOS_Contracts", filtro=filtro)
    else:
        return list()


def Contract_Create(CRM:SuiteCRM.SuiteCRM, contract_data:dict) -> tuple[str,dict]:
    if contract_data:
        s, d = CRM.PostData("AOS_Contracts", parametros=contract_data)
        if s:
            logger.critical(f"Contrato não foi criado. erro:{s}, dados:{contract_data}")
        else:
            logger.info(f"Contrato foi criado. dados:{contract_data}")
        return s, d
    else:
        return 'Sem informação', None
    

def Contract_Update(CRM:SuiteCRM.SuiteCRM, contract_data:dict) -> tuple[str,dict]:
    if contract_data:
        s, d = CRM.PutData("AOS_Contracts", parametros=contract_data)
        if s:
            logger.critical(f"Contrato não foi atualizado. erro:{s}, dados:{contract_data}")
        else:
            logger.info(f"Contrato foi atualizado. dados:{contract_data}")
        return s, d
    else:
        return "Sem Informação", None


def Contract_Delete(CRM:SuiteCRM.SuiteCRM, crm_id:str=None, numero:str=None) -> bool:
    if crm_id:
        s = CRM.DeleteData("AOS_Contracts", parametros={'id':crm_id})
        if s:
            logger.info(f"Contrato foi deletado. id:{crm_id}")
        else:
            logger.critical(f"Contrato não foi deletado. id:{crm_id}")
        return s
    elif numero:
        contrato = Contract_Get(CRM, numero=numero)
        if contrato:
            if len(contrato) == 1:
                return Contract_Delete(CRM=CRM, crm_id=contrato[0]['id'])
        logger.critical(f"Contrato não foi encontrado para deletar, numero:{numero}")
    return False


def Contract_AssociaAccounts(CRM:SuiteCRM.SuiteCRM, crm_contract_id:str, crm_account_id:str) -> bool:
    return CRM.AssociateData("contracts", base_record_id=crm_contract_id, relate_module="accounts", relate_record_ids=crm_account_id)


def Contract_AssociaGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_contract_id:str, crm_sec_grup_ids:str) -> bool:
    return CRM.AssociateData("contracts", base_record_id=crm_contract_id, relate_module="security-groups", relate_record_ids=crm_sec_grup_ids)
    

def Contract_RemoveGrupoSeguranca(CRM:SuiteCRM.SuiteCRM, contract_id:str, grupos:str) -> None:
    if grupos:
        for sec_g in grupos.split(','):
            _ = CRM.Desassocia(base_module="contracts", base_record_id=contract_id, relate_module="security-groups", relate_record_id=sec_g)


def Ticket_Create(CRM:SuiteCRM.SuiteCRM, ticket_data:dict) -> tuple[str,dict]:
    if ticket_data:
        return CRM.PostData("tickets", parametros=ticket_data)
    else:
        return "Sem informação", None


def BOAccounts(CRM) -> list[dict]:
    return CRM.GetData("GCR_ContaBackoffice", filtro={})
    

def BOAccount_Get(CRM:SuiteCRM.SuiteCRM, filtro:dict) -> list[dict]:
    if filtro:
        return CRM.GetData("GCR_ContaBackoffice", filtro=filtro)
    else:
        return list()


def BOAccount_Create(CRM:SuiteCRM.SuiteCRM, boaccount_data:dict) -> tuple[str,dict]:
    if boaccount_data:
        return CRM.PostData("GCR_ContaBackoffice", parametros=boaccount_data)
    else:
        return "Sem informação", None


def BOAccount_Update(CRM:SuiteCRM.SuiteCRM, contaBO_data:dict) -> tuple[str,dict]:
    if contaBO_data:
        return CRM.PutData("GCR_ContaBackoffice", parametros=contaBO_data)
    else:
        return "Sem informação", None
    

def BOAccount_RemoveGrupoSeguranca(CRM:SuiteCRM.SuiteCRM, bo_account_id:str, grupos:str) -> None:
    if grupos:
        for sec_g in grupos.split(','):
            _ = CRM.Desassocia(base_module="GCR_ContaBackoffice", base_record_id=bo_account_id, relate_module="security-groups", relate_record_id=sec_g)


def BOAccount_getAccounts(CRM:SuiteCRM.SuiteCRM, bo_account_id:str) -> list[dict]:
    accounts = CRM.GetSubPanelData(parentModule="GCR_ContaBackoffice", parentId=bo_account_id, module="accounts", subpanel="gcr_contabackoffice_accounts")
    if accounts and len(accounts) > 0:
        return accounts
    else:
        return list()


def BOAccount_getContracts(CRM:SuiteCRM.SuiteCRM, bo_account_id:str) -> list:
    contracts = CRM.GetSubPanelData(parentModule="GCR_ContaBackoffice", parentId=bo_account_id, module="contracts", subpanel="gcr_contabackoffice_aos_contracts")
    if contracts and len(contracts) > 0:
        return contracts
    else:
        return []


def Task_Create(CRM:SuiteCRM.SuiteCRM, task_data:dict) -> tuple[str,dict]:
    if task_data:
        return CRM.PostData("tasks", parametros=task_data)
    else:
        return "Sem informação", None


def SecurityGroup_Get(CRM:SuiteCRM.SuiteCRM, name:str) -> tuple[str,dict]:
    if name:
        resp = CRM.GetData("security-groups", filtro={'name': name})
        resposta = list()
        for r in resp:
            if r['name'] != str(name):
                continue
            resposta.append(r)
        return None, resposta
    else:
        return "Sem informação", None


def Account_AssociaContatos(CRM:SuiteCRM.SuiteCRM, crm_account_id:str, crm_contact_ids:str) -> bool:
    return CRM.AssociateData("accounts", base_record_id=crm_account_id, relate_module="contacts", relate_record_ids=crm_contact_ids)


def Account_AssociaContracts(CRM:SuiteCRM.SuiteCRM, crm_account_id:str, crm_contract_ids:str) -> bool:
    return CRM.AssociateData("accounts", base_record_id=crm_account_id, relate_module="contracts", relate_record_ids=crm_contract_ids)


def Account_AssociaGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_account_id:str, crm_sec_grup_ids:str) -> bool:
    return CRM.AssociateData("accounts", base_record_id=crm_account_id, relate_module="security-groups", relate_record_ids=crm_sec_grup_ids)


def BOAccount_AssociaContracts(CRM:SuiteCRM.SuiteCRM, crm_id:str, crm_contract_ids:str) -> bool:
    return CRM.AssociateData(base_module="GCR_ContaBackoffice", base_record_id=crm_id, relate_module="contracts", relate_record_ids=crm_contract_ids)


def BOAccount_AssociaBU(CRM:SuiteCRM.SuiteCRM, crm_id:str, crm_account_ids:str) -> bool:
    return CRM.AssociateData(base_module="GCR_ContaBackoffice", base_record_id=crm_id, relate_module="accounts", relate_record_ids=crm_account_ids)


def BOAccount_AssociaContacts(CRM:SuiteCRM.SuiteCRM, crm_id:str, crm_contact_ids:str) -> bool:
    return CRM.AssociateData(base_module="GCR_ContaBackoffice", base_record_id=crm_id, relate_module="contacts", relate_record_ids=crm_contact_ids)


def Contact_AssociaGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_contact_id:str, crm_sec_grup_ids:str) -> bool:
    return CRM.AssociateData("contacts", base_record_id=crm_contact_id, relate_module="security-groups", relate_record_ids=crm_sec_grup_ids)

