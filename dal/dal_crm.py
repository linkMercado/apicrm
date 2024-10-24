# encoding: utf-8
# -*- coding: utf-8 -*-
#


from apicrm import LOGGER as logger
from apicrm import SUITECRM as SuiteCRM
from apicrm import CRMPOOL as mysql_pool


def getPoolInfo():
    return mysql_pool.getPoolInfo()


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


def Colaboradores(CRM) -> list[dict]:
    return CRM.GetData("users", filtro={})
    

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
        return 'sem dados para cadastrar', dict()


def Account_Update(CRM:SuiteCRM.SuiteCRM, account_data:dict) -> tuple[str,dict]:
    if account_data:
        s, d = CRM.PutData("accounts", parametros=account_data)
        if s:
            logger.critical(f"Account não foi atualizado. erro:{s}, dados:{account_data}")
        else:
            logger.info(f"Account foi atualizado. dados:{account_data}")
        return s, d
    else:
        return "Sem informação", dict()


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


def Account_AssociaContatos(CRM:SuiteCRM.SuiteCRM, crm_account_id:str, crm_contact_ids:str) -> None:
    CRM.AssociateData("accounts", base_record_id=crm_account_id, relate_module="contacts", relate_record_ids=crm_contact_ids)


def Account_AssociaContracts(CRM:SuiteCRM.SuiteCRM, crm_account_id:str, crm_contract_ids:str) -> None:
    CRM.AssociateData("accounts", base_record_id=crm_account_id, relate_module="contracts", relate_record_ids=crm_contract_ids)


def Account_AssociaGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_account_id:str, crm_sec_grup_ids:str) -> None:
    CRM.AssociateData("accounts", base_record_id=crm_account_id, relate_module="security-groups", relate_record_ids=crm_sec_grup_ids)


def Account_GetGruposSeguranca(CRM:SuiteCRM.SuiteCRM, account_id:str) -> list[dict]:
    grupos_sec = CRM.GetSubPanelData(parentModule="accounts", parentId=account_id, module="security-groups", subpanel="securitygroups")
    return grupos_sec if grupos_sec else list()


def Account_RemoveGrupoSeguranca(CRM:SuiteCRM.SuiteCRM, crm_account_id:str, grupos:str) -> None:
    CRM.Desassocia(base_module="accounts", base_record_id=crm_account_id, relate_module="security-groups", relate_record_ids=grupos)


def Account_GetContacts(CRM:SuiteCRM.SuiteCRM, crm_account_id:str, fulldata:bool=False) -> list[dict]:
    contacts = CRM.GetSubPanelData(parentModule="accounts", parentId=crm_account_id, module="contacts", subpanel="contacts")
    if fulldata:
        kontacts = list()
        for contact in contacts if contacts else list():
            k = Contact_Get(CRM, {'id': contact('id')})
            if k: 
                kontacts.extend(k)
        return kontacts
    else:
        return contacts if contacts else list()


def Account_GetContracts(CRM:SuiteCRM.SuiteCRM, crm_account_id:str, fulldata:bool=False) -> list[dict]:
    contracts = CRM.GetSubPanelData(parentModule="accounts", parentId=crm_account_id, module="contracts", subpanel="account_aos_contracts")
    if fulldata:
        contratos = list()
        for contract in contracts if contracts else list():
            k = Contract_Get(CRM, filtro={'id':contract['id']})
            if k:
                contratos.extend(k)
        return contratos
    return contracts if contracts else list()


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
        return list()


def User_getHierarquia(CRM:SuiteCRM.SuiteCRM, id:str) -> list:
    if id:
        return CRM.get_colaborador_hierarquia(id)
    else:
        return list()
    

def User_get_SecurityGroupHierarchyIds(CRM:SuiteCRM.SuiteCRM, id:str) -> str:
    if id:
        return CRM.get_securityGroupHierarchyId(id)
    else:
        return ""


def User_get_SecurityGroupId(CRM:SuiteCRM.SuiteCRM, user_id:str) -> str:
    if user_id:
        return CRM.get_securityGroupId(user_id=user_id)
    else:
        return ""


def Leads(CRM) -> list[dict]:
    return CRM.GetData("leads", filtro={})


def Lead_Get(CRM:SuiteCRM.SuiteCRM, filtro:dict) -> list[dict]:
    if filtro:
        return CRM.GetData("leads", filtro=filtro)
    else:
        return []


def Lead_Update(CRM:SuiteCRM.SuiteCRM, lead_data:dict) -> tuple[str,dict]:
    if lead_data:
        s, d = CRM.PutData("leads", parametros=lead_data)
        if s:
            logger.critical(f"Lead não foi atualizado. erro:{s}, dados:{lead_data}")
        else:
            logger.info(f"Lead foi atualizado. dados:{lead_data}")
        return s, d
    else:
        return "Sem informação", None


def Lead_AssociaGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_lead_id:str, crm_sec_grup_ids:str) -> bool:
    CRM.AssociateData("leads", base_record_id=crm_lead_id, relate_module="security-groups", relate_record_ids=crm_sec_grup_ids)


def Lead_RemoveGrupoSeguranca(CRM:SuiteCRM.SuiteCRM, crm_lead_id:str, grupos:str) -> None:
    CRM.Desassocia(base_module="leads", base_record_id=crm_lead_id, relate_module="security-groups", relate_record_ids=grupos)


def Lead_GetGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_lead_id:str) -> list[dict]:
    grupos_sec = CRM.GetSubPanelData(parentModule="leads", parentId=crm_lead_id, module="security-groups", subpanel="securitygroups")
    return grupos_sec if grupos_sec else list()


def Contacts(CRM) -> list[dict]:
    return CRM.GetData("contacts", filtro={})


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


def Contact_GetAccounts(CRM:SuiteCRM.SuiteCRM, crm_contact_id:str, fulldata:bool=False) -> list[dict]:
    accounts = CRM.GetSubPanelData(parentModule="contacts", parentId=crm_contact_id, module="contacts", subpanel="accounts")
    if fulldata:
        akounts = list()
        for account in accounts if accounts else list():
            k = Account_Get(CRM, filtro={'id':account['id']})
            if k:
                akounts.extend(k)
        return akounts
    else:
        return accounts if accounts else list()


def Contact_AssociaAccounts(CRM:SuiteCRM.SuiteCRM, crm_contact_id:str, crm_account_id:str) -> None:
    CRM.AssociateData("contacts", base_record_id=crm_contact_id, relate_module="accounts", relate_record_ids=crm_account_id)


def Contact_AssociaGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_contact_id:str, crm_sec_grup_ids:str) -> bool:
    CRM.AssociateData("contacts", base_record_id=crm_contact_id, relate_module="security-groups", relate_record_ids=crm_sec_grup_ids)


def Contact_RemoveGrupoSeguranca(CRM:SuiteCRM.SuiteCRM, crm_contact_id:str, grupos:str) -> None:
    CRM.Desassocia(base_module="contacts", base_record_id=crm_contact_id, relate_module="security-groups", relate_record_ids=grupos)


def Contact_GetGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_contact_id:str) -> list[dict]:
    grupos_sec = CRM.GetSubPanelData(parentModule="contacts", parentId=crm_contact_id, module="security-groups", subpanel="securitygroups")
    return grupos_sec if grupos_sec else list()


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


def Contract_AssociaAccounts(CRM:SuiteCRM.SuiteCRM, crm_contract_id:str, crm_account_id:str) -> None:
    CRM.AssociateData("contracts", base_record_id=crm_contract_id, relate_module="accounts", relate_record_ids=crm_account_id)


def Contract_GetGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_contract_id:str) -> list[dict]:
    grupos_sec = CRM.GetSubPanelData(parentModule="contracts", parentId=crm_contract_id, module="security-groups", subpanel="securitygroups")
    return grupos_sec if grupos_sec else list()


def Contract_AssociaGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_contract_id:str, crm_sec_grup_ids:str) -> None:
    CRM.AssociateData("contracts", base_record_id=crm_contract_id, relate_module="security-groups", relate_record_ids=crm_sec_grup_ids)
    

def Contract_RemoveGrupoSeguranca(CRM:SuiteCRM.SuiteCRM, crm_contract_id:str, grupos:str) -> None:
    CRM.Desassocia(base_module="contracts", base_record_id=crm_contract_id, relate_module="security-groups", relate_record_ids=grupos)


def Tickets(CRM:SuiteCRM.SuiteCRM) -> list[dict]:
    return CRM.GetData("cases")


def Ticket_Create(CRM:SuiteCRM.SuiteCRM, ticket_data:dict) -> tuple[str,dict]:
    if ticket_data:
        return CRM.PostData("cases", parametros=ticket_data)
    else:
        return "Sem informação", None


def Ticket_Get(CRM:SuiteCRM.SuiteCRM, filtro:dict) -> list[dict]:
    if filtro:
        return CRM.GetData("cases", filtro=filtro)
    else:
        return list()


def Ticket_Update(CRM:SuiteCRM.SuiteCRM, ticket_data:dict) -> tuple[str,dict]:
    if ticket_data:
        s, d = CRM.PutData("cases", parametros=ticket_data)
        if s:
            logger.critical(f"Ticket não foi atualizado. erro:{s}, dados:{ticket_data}")
        else:
            logger.info(f"Ticket foi atualizado. dados:{ticket_data}")
        return s, d
    else:
        return "Sem informação", None


def Ticket_AssociaGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_ticket_id:str, crm_sec_grup_ids:str) -> None:
    CRM.AssociateData("cases", base_record_id=crm_ticket_id, relate_module="security-groups", relate_record_ids=crm_sec_grup_ids)


def Ticket_RemoveGrupoSeguranca(CRM:SuiteCRM.SuiteCRM, crm_ticket_id:str, grupos:str) -> None:
    CRM.Desassocia(base_module="cases", base_record_id=crm_ticket_id, relate_module="security-groups", relate_record_ids=grupos)


def Ticket_GetGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_ticket_id:str) -> list[dict]:
    grupos_sec = CRM.GetSubPanelData(parentModule="cases", parentId=crm_ticket_id, module="security-groups", subpanel="securitygroups")
    return grupos_sec if grupos_sec else list()


def Opportunities(CRM:SuiteCRM.SuiteCRM) -> list[dict]:
    return CRM.GetData("opportunities")


def Opportunity_Create(CRM:SuiteCRM.SuiteCRM, opportunity_data:dict) -> tuple[str,dict]:
    if opportunity_data:
        return CRM.PostData("opportunities", parametros=opportunity_data)
    else:
        return "Sem informação", None


def Opportunity_Get(CRM:SuiteCRM.SuiteCRM, filtro:dict) -> list[dict]:
    if filtro:
        return CRM.GetData("opportunities", filtro=filtro)
    else:
        return list()


def Opportunity_Update(CRM:SuiteCRM.SuiteCRM, opportunity_data:dict) -> tuple[str,dict]:
    if opportunity_data:
        s, d = CRM.PutData("opportunities", parametros=opportunity_data)
        if s:
            logger.critical(f"Oportunidade não foi atualizado. erro:{s}, dados:{opportunity_data}")
        else:
            logger.info(f"Oportunidade foi atualizada. dados:{opportunity_data}")
        return s, d
    else:
        return "Sem informação", None


def Opportunity_AssociaGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_opportunity_id:str, crm_sec_grup_ids:str) -> None:
    CRM.AssociateData("opportunities", base_record_id=crm_opportunity_id, relate_module="security-groups", relate_record_ids=crm_sec_grup_ids)


def Opportunity_RemoveGrupoSeguranca(CRM:SuiteCRM.SuiteCRM, crm_opportunity_id:str, grupos:str) -> None:
    CRM.Desassocia(base_module="opportunities", base_record_id=crm_opportunity_id, relate_module="security-groups", relate_record_ids=grupos)


def Opportunity_GetGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_opportunity_id:str) -> list[dict]:
    grupos_sec = CRM.GetSubPanelData(parentModule="opportunities", parentId=crm_opportunity_id, module="security-groups", subpanel="securitygroups")
    return grupos_sec if grupos_sec else list()


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
    

def BOAccount_AssociaGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_boaccount_id:str, crm_sec_grup_ids:str) -> None:
    CRM.AssociateData("GCR_ContaBackoffice", base_record_id=crm_boaccount_id, relate_module="security-groups", relate_record_ids=crm_sec_grup_ids)


def BOAccount_RemoveGrupoSeguranca(CRM:SuiteCRM.SuiteCRM, crm_boaccount_id:str, grupos:str) -> None:
    CRM.Desassocia(base_module="GCR_ContaBackoffice", base_record_id=crm_boaccount_id, relate_module="security-groups", relate_record_ids=grupos)


def BOAccount_GetGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_boaccount_id:str) -> list[dict]:
    grupos_sec = CRM.GetSubPanelData(parentModule="GCR_ContaBackoffice", parentId=crm_boaccount_id, module="security-groups", subpanel="securitygroups")
    return grupos_sec if grupos_sec else list()


def BOAccount_GetAccounts(CRM:SuiteCRM.SuiteCRM, crm_boaccount_id:str, fulldata:bool=False) -> list[dict]:
    accounts = CRM.GetSubPanelData(parentModule="GCR_ContaBackoffice", parentId=crm_boaccount_id, module="accounts", subpanel="gcr_contabackoffice_accounts")
    if fulldata:
        akounts = list()
        for account in accounts if accounts else list():
            k = Account_Get(CRM, filtro={'id':account['id']})
            if k:
                akounts.extend(k)
        return akounts
    else:
        return accounts if accounts else list()


def BOAccount_GetContracts(CRM:SuiteCRM.SuiteCRM, crm_boaccount_id:str, fulldata:bool=False) -> list:
    contracts = CRM.GetSubPanelData(parentModule="GCR_ContaBackoffice", parentId=crm_boaccount_id, module="contracts", subpanel="gcr_contabackoffice_aos_contracts")
    if fulldata:
        kontracts = list()
        for contract in contracts if contracts else list():
            k = Contract_Get(CRM, filtro={'id':contract['id']})
            if k:
                kontracts.extend(k)
        return kontracts
    else:
        return contracts if contracts else list()


def BOAccount_AssociaContracts(CRM:SuiteCRM.SuiteCRM, crm_id:str, crm_contract_ids:str) -> None:
    CRM.AssociateData(base_module="GCR_ContaBackoffice", base_record_id=crm_id, relate_module="contracts", relate_record_ids=crm_contract_ids)


def BOAccount_DesassociaContracts(CRM:SuiteCRM.SuiteCRM, crm_id:str, crm_contract_ids:str) -> None:
    CRM.Desassocia(base_module="GCR_ContaBackoffice", base_record_id=crm_id, relate_module="contracts", relate_record_ids=crm_contract_ids)


def BOAccount_AssociaBU(CRM:SuiteCRM.SuiteCRM, crm_id:str, crm_account_ids:str) -> None:
    CRM.AssociateData(base_module="GCR_ContaBackoffice", base_record_id=crm_id, relate_module="accounts", relate_record_ids=crm_account_ids)


def BOAccount_DesassociaBU(CRM:SuiteCRM.SuiteCRM, crm_id:str, grupos:str) -> None:
    CRM.Desassocia(base_module="GCR_ContaBackoffice", base_record_id=crm_id, relate_module="accounts", relate_record_ids=grupos)


def BOAccount_AssociaContacts(CRM:SuiteCRM.SuiteCRM, crm_id:str, crm_contact_ids:str) -> None:
    CRM.AssociateData(base_module="GCR_ContaBackoffice", base_record_id=crm_id, relate_module="contacts", relate_record_ids=crm_contact_ids)


def Tasks(CRM:SuiteCRM.SuiteCRM) -> list[dict]:
    return CRM.GetData("tasks")


def Task_Get(CRM:SuiteCRM.SuiteCRM, filtro:dict) -> list[dict]:
    if filtro:
        return CRM.GetData("tasks", filtro=filtro)
    else:
        return list()


def Task_Create(CRM:SuiteCRM.SuiteCRM, task_data:dict) -> tuple[str,dict]:
    if task_data:
        return CRM.PostData("tasks", parametros=task_data)
    else:
        return "Sem informação", None


def Task_Update(CRM:SuiteCRM.SuiteCRM, task_data:dict) -> tuple[str,dict]:
    if task_data:
        s, d = CRM.PutData("tasks", parametros=task_data)
        if s:
            logger.critical(f"Tarefa não foi atualizada. erro:{s}, dados:{task_data}")
        else:
            logger.info(f"Tarefa foi atualizada. dados:{task_data}")
        return s, d
    else:
        return "Sem informação", None


def Task_AssociaGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_task_id:str, crm_sec_grup_ids:str) -> None:
    CRM.AssociateData("tasks", base_record_id=crm_task_id, relate_module="security-groups", relate_record_ids=crm_sec_grup_ids)


def Task_RemoveGrupoSeguranca(CRM:SuiteCRM.SuiteCRM, crm_task_id:str, grupos:str) -> None:
    CRM.Desassocia(base_module="tasks", base_record_id=crm_task_id, relate_module="security-groups", relate_record_ids=grupos)


def Task_GetGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_task_id:str) -> list[dict]:
    grupos_sec = CRM.GetSubPanelData(parentModule="tasks", parentId=crm_task_id, module="security-groups", subpanel="securitygroups")
    return grupos_sec if grupos_sec else list()


def Project_Get(CRM:SuiteCRM.SuiteCRM, filtro:dict) -> list[dict]:
    if filtro:
        return CRM.GetData("project", filtro=filtro)
    else:
        return list()


def Project_Create(CRM:SuiteCRM.SuiteCRM, project_data:dict) -> tuple[str,dict]:
    if project_data:
        return CRM.PostData("project", parametros=project_data)
    else:
        return "Sem informação", None


def Project_Update(CRM:SuiteCRM.SuiteCRM, project_data:dict) -> tuple[str,dict]:
    if project_data:
        s, d = CRM.PutData("project", parametros=project_data)
        if s:
            logger.critical(f"Projeto não foi atualizado. erro:{s}, dados:{project_data}")
        else:
            logger.info(f"Projeto foi atualizada. dados:{project_data}")
        return s, d
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


def Atividade_GetIDandName(cod:str=None, atv:str=None) -> tuple[str,str]:
    if cod:
        cmd = f"select id, name from gcr_titulos where cod_titulo_lm={cod} and deleted=0"
    elif atv:
        _atv = atv.replace("'","''")
        cmd = f"select id, name from gcr_titulos where name='{_atv}' and deleted=0"
    else:
        return None
    resp = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=False)
    if resp and len(resp) > 0:
        return resp[0]['id'], resp[0]['name']
    else:
        return None, None
    

def Atividade_GetCorpId(id:str) -> str:
    cmd = f"select cod_titulo_corp from gcr_titulos where id='{id}' and deleted=0"
    resp = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=False)
    if resp and len(resp) > 0:
        return resp[0]['cod_titulo_corp']
    else:
        return None
    