# encoding: utf-8
# -*- coding: utf-8 -*-
#

import re
from apicrm import LOGGER as logger
from apicrm import SUITECRM as SuiteCRM

def Delete(CRM:SuiteCRM.SuiteCRM, module:str, entity_data:dict) -> tuple[bool, dict]:
    critica = CRM.critica_parametros(module, 'DELETE', entity_data)
    if critica:
        return False, { 'msg': critica }
    d = CRM.DeleteData(module, parametros=entity_data)
    return d, { 'msg': None } if d else { 'msg': 'Erro' }


def Post(CRM:SuiteCRM.SuiteCRM, module:str, entity_data:dict) -> tuple[bool, dict]:
    critica = CRM.critica_parametros(module, 'POST', entity_data)
    if critica:
        return False, { 'msg': critica }
    _, r = CRM.PostData(module, parametros=entity_data)
    _id = r.get("id") if r else None
    if _id:
        return True, {'data': {'id':_id} }
    return False, { 'msg':'ERRO !' }


def Put(CRM:SuiteCRM.SuiteCRM, module:str, entity_data:dict) -> tuple[bool, dict]:
    critica = CRM.critica_parametros(module, 'PUT', entity_data)
    if critica:
        return False, { 'msg': critica }
    _, r = CRM.PutData(module, parametros=entity_data)
    _id = r.get("id") if r else None
    if _id:
        return True, {'data': {'id':_id} }
    return False, { 'msg':'ERRO !' }


def Get(CRM:SuiteCRM.SuiteCRM, module:str, filtro:dict=dict()) -> tuple[bool, dict]:
    critica = CRM.critica_parametros(module, 'GET', filtro)
    if critica:
        return False, { 'msg': critica }
    return True, { 'data': CRM.GetData(module, filtro=filtro) }


def Accounts(CRM) -> dict:
    return CRM.GetData("accounts", filtro={})
    

def Account_Get(CRM:SuiteCRM.SuiteCRM, id:str=None, id_conta_lm:str=None, buid:str=None, id_cliente:str=None, status:str=None) -> dict:
    filtro = dict()
    if id:
        filtro['id'] = id
    if id_conta_lm:
        filtro['id_conta_lm_c'] = str(id_conta_lm)
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
        elif id_conta_lm and r['id_conta_lm_c'] != str(id_conta_lm):
            continue
        elif id_cliente and r['id_cliente_c'] != str(id_cliente):
            continue
        elif buid and r['bu_id_c'] != str(buid):
            continue
        elif status and r['status_c'] != str(status):
            continue
        resposta.append(r)
    return resposta


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


def Account_RemoveGrupoSeguranca(CRM:SuiteCRM.SuiteCRM, account_id:str, grupos:str):
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


def Account_getContacts(CRM:SuiteCRM.SuiteCRM, account_id:str):
    contacts = CRM.get_contaContacts(account_id)
    if contacts and len(contacts) > 0:
        return contacts
    else:
        return None


def User_Get(CRM:SuiteCRM.SuiteCRM, id:str=None, username:str=None, email:str=None) -> dict:
    return CRM.getColaborador(id=id, username=username, email=email)


def Contact_Get(CRM:SuiteCRM.SuiteCRM, id:str=None, fname:str=None, lname:str=None, email:str=None, document:str=None, phone_work:str=None, mobile_phone:str=None, whatsapp:str=None) -> list[dict]:
    filtro = dict()
    if id:
        filtro['id'] = id
    if fname:
        filtro['first_name'] = fname
        __fname = re.sub('[^a-zA-Z0-9]', '', fname)
    else:
        __fname = None
    if lname:
        filtro['last_name'] = lname
        __lname = re.sub('[^a-zA-Z0-9]', '', lname)
    else:
        __lname = None
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
    if phone_work:
        filtro['phone_work'] = SuiteCRM.format_phone(phone_work)
        __phone = SuiteCRM.format_phone(phone_work)
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
        # calclula nota máxima
        max_nota = 0
        max_nota += 1 if id else 0
        max_nota += 1 if fname or lname else 0
        max_nota += 1 if email else 0
        max_nota += 1 if document else 0
        max_nota += 1 if phone_work else 0
        max_nota += 1 if mobile_phone else 0
        max_nota += 1 if whatsapp else 0

        crm_contatos = CRM.GetData("contacts", filtro=filtro)
        # se retornou mais de um, qual dos contatos ?
        resp = list()
        for crm_contato in crm_contatos if crm_contatos else []:
            nota = 0 
            # se FirstName e LastName forem informados, ambos tem que ser iguais
            _fname = crm_contato.get('first_name','')
            _lname = crm_contato.get('last_name','')
            if _fname and __fname and _lname and __lname:
                if (__fname and (re.sub('[^a-zA-Z0-9]', '', _fname).upper() == __fname.upper())) \
                   and (__lname and (re.sub('[^a-zA-Z0-9]', '', _lname).upper() == __lname.upper())):
                    nota = 1
                else:
                    continue
            nota += 1 if id == crm_contato['id'] else 0
            nota += 1 if __document and re.sub('[^0-9]', '', crm_contato.get('cpf_c','')) == __document else 0
            nota += 1 if __email and crm_contato.get('email1') == __email else 0
            nota += 1 if __phone and SuiteCRM.format_phone(crm_contato.get('phone_work'), internacional=True) == __phone else 0
            nota += 1 if __mobile_phone and SuiteCRM.format_phone(crm_contato.get('mobile_phone'), internacional=True) == __mobile_phone else 0
            nota += 1 if __whatsapp and SuiteCRM.format_phone(crm_contato.get('phone_fax'), internacional=True) == __whatsapp else 0
            if nota > 1 or nota == max_nota:
                achou = False
                for r in resp:
                    achou = achou or (r['id'] == crm_contato['id'])
                    if achou:
                        break
                if not achou:
                    resp.append(crm_contato)
        if len(resp) > 1:
            # por enquanfo, quando tem mais de um, diz que tem nenhum
            logger.warning(f"Vários contatos com a chave: fname={fname}, lname={lname}, email={email}, document={document}, phone_work={phone_work}, mobile_phone={mobile_phone}, whatsapp={whatsapp}")
            resp = list()
        return resp
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


def Contract_Get(CRM:SuiteCRM.SuiteCRM, id:str=None, name:str=None, numero:str=None) -> dict:
    filtro = dict()
    if id:
        filtro['id'] = id
    if name:
        filtro['name'] = name
    if numero:
        filtro['reference_code'] = numero
    if filtro:       
        resp = CRM.GetData("AOS_Contracts", filtro=filtro)
        resposta = list()
        for r in resp:
            if id and r['id'] != id:
                continue
            if name and r['name'] != name:
                continue
            if numero and r['reference_code'] != numero:
                continue
            resposta.append(r)
        return resposta    
    else:
        return None


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


def Cria_contato(CRM:SuiteCRM.SuiteCRM, parametros) -> tuple[str,dict]:
    return CRM.cria_contato(**parametros)


def Ticket_Create(CRM:SuiteCRM.SuiteCRM, ticket_data:dict) -> tuple[str,dict]:
    if ticket_data:
        return CRM.PostData("tickets", parametros=ticket_data)
    else:
        return "Sem informação", None


def BOAccounts(CRM) -> dict:
    return CRM.GetData("GCR_ContaBackoffice", filtro={})
    

def BOAccount_Get(CRM:SuiteCRM.SuiteCRM, id_conta_lm:str) -> tuple[str,dict]:
    if id_conta_lm:
        resp = CRM.GetData("GCR_ContaBackoffice", filtro={'id_conta_lm': id_conta_lm})
        resposta = list()
        for r in resp:
            if r['id_conta_lm'] != str(id_conta_lm):
                continue
            resposta.append(r)
        return None, resposta
    else:
        return "Sem informação", None


def BOAccount_Update(CRM:SuiteCRM.SuiteCRM, contaBO_data:dict) -> tuple[str,dict]:
    if contaBO_data:
        return None, CRM.PutData("GCR_ContaBackoffice", parametros=contaBO_data)
    else:
        return "Sem informação", None
    
    
def BOAccount_RemoveGrupoSeguranca(CRM:SuiteCRM.SuiteCRM, bo_account_id:str, grupos:str):
    if grupos:
        for sec_g in grupos.split(','):
            _ = CRM.Desassocia(base_module="GCR_ContaBackoffice", base_record_id=bo_account_id, relate_module="security-groups", relate_record_id=sec_g)



def BOAccount_getAccounts(CRM:SuiteCRM.SuiteCRM, bo_account_id:str):
    accounts = CRM.get_BOcontaAccounts(bo_account_id)
    if accounts and len(accounts) > 0:
        return accounts
    else:
        return None

    

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


def BOAccount_AssociaContracts(CRM:SuiteCRM.SuiteCRM, crm_id:str, crm_contract_ids:str) -> bool:
    return CRM.AssociateData(base_module="GCR_ContaBackoffice", base_record_id=crm_id, relate_module="contracts", relate_record_ids=crm_contract_ids)


def BOAccount_AssociaBU(CRM:SuiteCRM.SuiteCRM, crm_id:str, crm_account_ids:str) -> bool:
    return CRM.AssociateData(base_module="GCR_ContaBackoffice", base_record_id=crm_id, relate_module="accounts", relate_record_ids=crm_account_ids)


def BOAccount_AssociaContacts(CRM:SuiteCRM.SuiteCRM, crm_id:str, crm_contact_ids:str) -> bool:
    return CRM.AssociateData(base_module="GCR_ContaBackoffice", base_record_id=crm_id, relate_module="contacts", relate_record_ids=crm_contact_ids)


def Contact_AssociaGruposSeguranca(CRM:SuiteCRM.SuiteCRM, crm_contact_id:str, crm_sec_grup_ids:str) -> bool:
    return CRM.AssociateData("contacts", base_record_id=crm_contact_id, relate_module="security-groups", relate_record_ids=crm_sec_grup_ids)

