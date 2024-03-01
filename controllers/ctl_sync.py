
from apicrm import LOGGER as logger
from apicrm import SUITECRM as SuiteCRM 

from models import mod_crm
from dal import dal_lm
from dal import dal_crm


def sync_account(buid:str, userid:str=None) -> bool:
    CRM = SuiteCRM.SuiteCRM(logger) 
    budata = dal_lm.GetBU(buid)
    if budata:
        suite_id = budata.get('suite_id')
        entity_data = mod_crm.Account.fromBO(budata).__dict__
        if suite_id: 
            # se tem suite_id, atualiza !
            status, _acc = dal_crm.Put(CRM, "accounts", entity_data=entity_data)
            return True if status and _acc else False
        elif budata.get('status') == 0:
            # se não tem suite_id e a BU está ativa, cria !
            if userid:
                user = dal_lm.GetUser(userid)
                status, _user = dal_crm.Get(CRM, 'users', {'email': user['email']})
                if _user and len(_user.get('data',[])) == 1:
                    entity_data['assigned_user_id'] = _user.get('data')[0].get('id')
                else:
                    logger.warning(f"User não encontrado no SuiteCRM u:{user}")
            status, _acc = dal_crm.Post(CRM, "accounts", entity_data=entity_data)
            if status and _acc:
                suite_id = _acc.get('data',{}).get('id')
                dal_lm.PutSuiteID(buid, suite_id)
                # associa os autorizadores(contatos) à conta criada
                autorizadores = dal_lm.GetAutorizadores(buid)
                if autorizadores:
                    lista_contatos = ""
                    for autorizador in autorizadores:
                        # verifica se autorizador está no CRM
                        filtro = {'name': autorizador['name']}
                        if autorizador['email']:
                            filtro['email'] = autorizador['email']
                        if autorizador['document']:
                            filtro['cpf_c'] = autorizador['document']
                        if autorizador['phone']:
                            filtro['phone_work'] = autorizador['phone']
                        if autorizador['mobile_phone']:
                            filtro['phone_mobile'] = autorizador['mobile_phone']
                        status, contato = dal_crm.Get(CRM, "contacts", filtro)
                        if not status:
                            logger.debug("Erro critico ao pegar o contato")
                            continue
                        if contato and len(contato.get('data',[])) == 0:
                            contato = dal_crm.Cria_contato(CRM, mod_crm.Contact().fromBO(autorizador).__dict__)
                            contato_id = contato['data']['saveRecord']['record']['_id']
                        else:
                            contato_id = contato['data'][0]['id']                    
                        lista_contatos += f"{contato_id},"
                    # associa os contatos à conta
                    r = dal_crm.Associa_contatos(CRM, suite_id, lista_contatos[:-1])
                    if not r:
                        logger.debug("Associação com problemas")
                return True
            logger.critical(f"Erro ao criar Account no SuiteCRM BU:{buid}")
            return False
        else:
            # nada a fazer
            return True
    logger.debug(f"BU id {buid} não encontrada")        
    return False
    

def sync_bo():
    CRM = SuiteCRM.SuiteCRM(logger) 
    s, accounts = dal_crm.Get(CRM, "accounts")
    for conta in accounts.get('data',[]):
        buid = conta.get('bu_id_c')
        if buid:
            suite_id = conta.get('id')
            dal_lm.PutSuiteID(buid, suite_id)
            """
            ,"assigned_user_name":
            ,"full_name":""
            ,"salutation":
            ,"first_name":
            ,"last_name":
            ,"phone_work":
            ,"phone_mobile":""
            ,"tipocontato_c":
            ,"contatoprincipal_c":
            ,"title":""
            ,"department":""
            ,"cpf_c":""
            ,"account_name":""
            ,"phone_fax":""
            ,"email_addresses":[]
            ,"primary_address":""
            ,"primary_address_street":""
            ,"primary_address_city":""
            ,"primary_address_state":""
            ,"primary_address_postalcode":""
            ,"primary_address_country":""
            ,"alt_address":""
            ,"alt_address_street":""
            ,"alt_address_city":""
            ,"alt_address_state":""
            ,"alt_address_postalcode":""
            ,"alt_address_country":""
            ,"description":""
            ,"lead_source":""
            ,"report_to_name":""
            ,"campaign_name":""
            ,"facebook_c":""
            ,"instagram_c":""
            ,"date_entered":"",
            "date_modified":""
            {"operationName":"createProcess","variables":{"input":{"type":"record-select","options":{"action":"record-select","module":"accounts","id":"b96c4f5b-3320-b071-6a90-65a87ed0463c","payload":{"baseModule":"accounts","baseRecordId":"b96c4f5b-3320-b071-6a90-65a87ed0463c","linkField":"contacts","relateModule":"contacts","relateRecordIds":["101bf212-dd05-5f60-d2b2-65a1d8252cca"]}}}},"query":"mutation createProcess($input: createProcessInput!) {\n  createProcess(input: $input) {\n    process {\n      _id\n      status\n      async\n      type\n      messages\n      data\n      __typename\n    }\n    clientMutationId\n    __typename\n  }\n}"}
            """


def sync_contatos():
    CRM = SuiteCRM.SuiteCRM(logger) 
    bo_contatos = dal_lm.GetContatos()
    for contato in bo_contatos:
        _, k1 = dal_crm.Get(CRM, "contacts", filtro={'email':contato['email']}) if contato['email'] else False, None
        _, k2 = dal_crm.Get(CRM, "contacts", filtro={'cpf_c':contato['document']}) if contato['document'] else False, None
        #_, k3 = dal_crm.Get("accounts", filtro={'mobile_phone':contato['mobile_phone']}) if contato['mobile_phone'] else False, None
        #_, k4 = dal_crm.Get("accounts", filtro={'phone_work':contato['phone']}) if contato['phone'] else False, None
        #_, k5 = dal_crm.Get("accounts", filtro={'phone_fax':contato['mobile_phone']}) if contato['mobile_phone'] else False, None
        #_, k6 = dal_crm.Get("accounts", filtro={'phone_work':contato['phone']})if contato['phone'] else False, None
        #_, k7 = dal_crm.Get("accounts", filtro={'phone_work':contato['mobile_phone']}) if contato['mobile_phone'] else False, None
        entity_data = {
            "first_name": contato['name'],
            "phone_mobile": contato['mobile_phone'],
            "phone_work": contato['phone'],
            "phone_fax": contato['mobile_phone'],
            "email": contato['email'],
            "account_id": contato['suite_id'],
            "cpf_c": contato['document'],
            "tipocontato_c": ["Autorizador"]
        }
        if not (    (k1 and len(k1.get('data',[])) > 0)  \
                 or (k2 and len(k2.get('data',[])) > 0) \
        #        or (k3 and len(k3.get('data',[])) > 0) \
        #        or (k4 and len(k4.get('data',[])) > 0) \
        #        or (k5 and len(k5.get('data',[])) > 0) \
        #        or (k6 and len(k6.get('data',[])) > 0) \
        #        or (k7 and len(k7.get('data',[])) > 0) \
            ):
            dal_crm.Post(CRM, "contacts", entity_data=entity_data)

# sync_bo()
# jb
# sync_account(19825816) # bysdev

# sync_contatos()