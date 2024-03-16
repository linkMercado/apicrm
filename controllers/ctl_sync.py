
from apicrm import LOGGER as logger
from apicrm import SUITECRM as SuiteCRM 
from lm_packages.Extras import TAB, CRLF

from models import mod_crm
from dal import dal_lm
from dal import dal_crm

WATSON_UserID = 'a2fc0fc9-cb48-39c3-2bb2-658b42a377d7'


def sync_BO2CRM_Account(account_id:str, userid:str=None, crm_user_id:str=None) -> tuple[dict, dict]:
    _crm_user_id = None
    if int(account_id) <= 1:
        raise ValueError(f"account_id inválido: {account_id}, deve ser maior do que 1")

    CRM = SuiteCRM.SuiteCRM(logger)     
    respostas:dict = dict()
    suite_ids: dict = dict()

    # pega a lista dos assigneds que estão no CRM para as empresas dessa conta
    # se a conta existe no CRM, mantem o assigned_user_id
    if crm_user_id is None:
        crm_accounts = dal_crm.Account_Get(CRM, id=None, account_id=account_id)
        if crm_accounts and len(crm_accounts) > 0:
            crm_user_ids = dict()
            for crm_account in crm_accounts:
                assigned_id = crm_account.get('assigned_user_id')
                if assigned_id == WATSON_UserID:
                    crm_user_ids[assigned_id] = 0
                else:
                    crm_user_ids[assigned_id] = crm_user_ids.get(assigned_id,0) + 1
            ov = -1
            for k, v in crm_user_ids.items():
                if v > ov:
                    ov = v
                    _crm_user_id = k
        else:
            if userid:
                user = dal_lm.GetUser(userid)
                crm_user = dal_crm.User_Get(CRM, email=user['email'])
                _crm_user_id = crm_user.get('data',{}).get('saveRecord',{}).get('record',{}).get("_id") if crm_user else None
                if not _crm_user_id:
                    logger.critical(f"User não encontrado no SuiteCRM u:{user}")
        crm_accounts = None
    else:
        _crm_user_id = crm_user_id

    # trata os Clientes associados à conta
    lista_contatos = ""
    autorizadores = dal_lm.GetAutorizadores(account_id)
    if autorizadores:
        for autorizador in autorizadores:
            # verifica se autorizador está no CRM
            crm_contato = dal_crm.Contact_Get(CRM, name=autorizador['name'], email=autorizador['email'], document=autorizador['document'], phone=autorizador['phone'], mobile_phone=autorizador['mobile_phone'])
            # cria o contato ?
            if not crm_contato:
                crm_contato = dal_crm.Contact_Create(CRM, mod_crm.Contact().fromBO(autorizador).__dict__)
                contato_id = crm_contato['data']['saveRecord']['record']['_id']
                logger.info(f"Contato criado no SuiteCRM c:{autorizador}, id:{contato_id}")
            else:
                contato_id = crm_contato[0]['id']                    
            lista_contatos += f"{contato_id},"

    for budata in dal_lm.GetAccountBUs(account_id):
        suite_id = budata.get('suite_id')
        bu_id = budata.get('id')
        account_data = mod_crm.Account.fromBO(budata).__dict__
        account_data['assigned_user_id'] = _crm_user_id
        respostas[bu_id] = ""
        suite_ids[bu_id] = suite_id

        if account_data['atividade_principal_c'] == 'Negocios':
            respostas[bu_id] = "Rever atividade Principal"
            suite_ids[bu_id] = None
            continue

        # está no CRM ?
        if suite_id:
            _crmdata = dal_crm.Account_Get(CRM, id=suite_id)
            if len(_crmdata) == 1:
                crmdata = _crmdata[0]
            else:
                crmdata = None
            # confirma !
            if crmdata:
                # mantém o mesmo assigned_user_id ?
                if crm_user_id:
                    account_data['assigned_user_id'] = crm_user_id
                elif not userid:
                    account_data['assigned_user_id'] = crmdata['assigned_user_id']

                # se inativo CRM e BO, skip
                if crmdata.get('status_c') == 'Inativo' and budata.get('status') != 0:
                    respostas[bu_id] += 'Não atualizado, Inativo.'
                    suite_ids[bu_id] = None
                    continue
                
                # atualiza !
                atualizou = dal_crm.Account_Update(CRM, account_data)
                respostas[bu_id] += 'Atualizado.' if atualizou else 'Erro ao atualizar.'
            else:
                # estranho não achar no CRM pois tinha suite_id, marca para criar
                suite_id = None
                suite_ids[bu_id] = suite_id
                account_data['id'] = suite_id

        # precisa criar no CRM ?    
        if not suite_id:
            if budata.get('status') != 0:
                # se não está no CRM e BU está inativa, pula 
                respostas[bu_id] = 'Não sincronizado, inativo no BO.'
                suite_ids[bu_id] = None
                continue

            # verifica se tem conta com o mesmo endereço e com o mesmo id_conta_lm
            _address = account_data.get('shipping_address_street','').replace(' ','').replace('-','').replace(',','')
            if _address:
                for _acc in dal_crm.Account_Get(CRM, id=None, account_id=account_id):
                    if _acc.get('shipping_address_street').replace(' ','').replace('-','').replace(',','') == _address:
                        suite_id = _acc.get('id')
                        account_data['id'] = suite_id
                        dal_lm.PutSuiteID(bu_id, suite_id)
                        suite_ids[bu_id] = suite_id
                        break
            else:
                respostas[bu_id] = 'Não sincronizado, sem endereço no BO.'
                continue

            if suite_id:
                suite_ids[bu_id] = suite_id
                atualizou = dal_crm.Account_Update(CRM, account_data)
                respostas[bu_id] += 'Atualizado.' if atualizou else 'Erro ao atualizar.'
            else:    
                # cria no CRM
                crm_account = dal_crm.Account_Create(CRM, account_data)
                if crm_account:
                    suite_id = crm_account.get('id')
                    dal_lm.PutSuiteID(bu_id, suite_id)
                    respostas[bu_id] += 'Criado e Atualizado.'
                    suite_ids[bu_id] = suite_id
                else:
                    respostas[bu_id] += 'Nao criou no CRM, VERIFICAR!'
                    suite_ids[bu_id] = None

        # associa os contatos à conta
        if lista_contatos:            
            r = dal_crm.Associa_contatos(CRM, suite_id, lista_contatos[:-1])
            if not r:
                logger.debug("Associação com problemas")
                respostas[bu_id] += ' - Associação dos Colaboradores com problemas.'
    return respostas, suite_ids


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
    

def sync_CRM2BO_Account() -> tuple[str: dict]:
    msg_tec:str = ""
    suite_ids = dict()
    CRM = SuiteCRM.SuiteCRM(logger)

    crm_accounts = dal_crm.Account_Get(CRM, id=None)
    bo_account_ids = dict()
    for crm_account in crm_accounts:
        buid = crm_account.get('bu_id_c')
        suite_id = crm_account.get('id')
        id_conta_lm = crm_account.get('id_conta_lm_c')
        assigned_user_id = crm_account.get('assigned_user_id')
        if buid:
            # já tem o código bo BO ?
            bo_suite_id = dal_lm.GetSuiteID(buid)
            if bo_suite_id == -1:
                msg_tec += f"O BUID da conta {crm_account.get('name')}, id:{suite_id} não foi encontrado no BO, Verificar !{CRLF}"
                bo_account_ids[id_conta_lm] = assigned_user_id
            elif bo_suite_id != suite_id:
                # se os códigos são diferentes, atualiza o código do CRM
                dal_lm.PutSuiteID(buid, suite_id)
                bo_account_ids[id_conta_lm] = assigned_user_id
        else:
            msg_tec += f"A conta {crm_account.get('name')}, id:{suite_id} está sem o BUID, Verificar !{CRLF}"
            bo_account_ids[id_conta_lm] = assigned_user_id

    # força a sincronização de todas os BO-Contas que subiram do CRM para o BO
    if bo_account_ids:
        for account_id, user_id in bo_account_ids:
            msg_list, buids_list = sync_BO2CRM_Account(account_id, user_id)
            suite_ids = {**suite_ids, **buids_list}
            resp += f"Account {account_id}:{CRLF}{TAB}{msg_list}"
    return resp, suite_ids



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

#w = sync_CRM2BO_Account()
#w = sync_BO2CRM_Account(279399)
#print(w)
            
#r = dict()
#r.update(sync_BO2CRM_Account('68108', crm_user_id='ad72ba17-3603-86fe-90c4-6565f5c5444b'))
#print(r)
#print() 
