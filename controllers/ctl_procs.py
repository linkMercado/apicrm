import re
import csv

from datetime import date, datetime
from apicrm import LOGGER as logger
from apicrm import SUITECRM as SuiteCRM 
from lm_packages.Extras import TAB, CRLF

from models import mod_crm
from dal import dal_lm
from dal import dal_crm

WATSON_UserID = 'a2fc0fc9-cb48-39c3-2bb2-658b42a377d7'


def cria_notificacao(business_unit_id:str, titulo:str, texto:str=None) -> str:
    """
    cria uma nota no CRM(business_unit_id:str, titulo:str, texto:str=None)
    """
    CRM = SuiteCRM.SuiteCRM(logger)

    crm_account = CRM.GetData("accounts",{'bu_id_c': business_unit_id})
    if crm_account:
        crm_account_id = crm_account[0].get('id')
        crm_nota = CRM.cria_note(parent_type="accounts", parent_id=crm_account_id, name=titulo, description=texto)
        crm_nota_id = crm_nota.get('data',{}).get('saveRecord',{}).get('record',{}).get('_id')
        msg = f"Nota {crm_nota_id} para a bu:{business_unit_id} criada."
    else:
        msg = f"Não exite conta para a bu:{business_unit_id}"    
    return msg  


def sync_BO2CRM_Account(account_id:str, userid:str=None, crm_user_id:str=None, gerente_relacionamento:str=None) -> tuple[dict, dict]:
    _crm_user_id = None
    if int(account_id) <= 1:
        raise ValueError(f"account_id inválido: {account_id}, deve ser maior do que 1")

    CRM = SuiteCRM.SuiteCRM(logger)     
    respostas:dict = dict()
    suite_ids:dict = dict()

    # pega a lista das contas do CRM
    # e escolhe o assigned_user_id que mais aparece (só deveria haver 1!)
    # e escolhe o gerente_relacionamento que mais aparece (só deveria haver 1!)
    # e escolhe a conta Master que mais aparece (só deveria haver 1!)
    _crm_user_id = WATSON_UserID
    _users_accounts_1users_ida = None
    _master_id = None
    crm_accounts = dal_crm.Account_Get(CRM, id=None, account_id=account_id)
    if crm_accounts and len(crm_accounts) > 0:
        crm_user_ids = dict()
        gerente_ids = dict()
        parent_ids = dict()
        for crm_account in crm_accounts:
            assigned_id = crm_account.get('assigned_user_id')
            if assigned_id == WATSON_UserID:
                crm_user_ids[assigned_id] = 0
            else:
                crm_user_ids[assigned_id] = crm_user_ids.get(assigned_id,0) + 1
            gerente_id = crm_account.get('users_accounts_1users_ida')
            if gerente_id:
                gerente_ids[gerente_id] = gerente_ids.get(gerente_id,0) + 1
            parent_id = crm_account.get('parent_id')
            if parent_id:
               parent_ids[parent_id] = parent_ids.get(parent_id,0) + 1
        # pega o assigned_user que tem mais
        ov = -1
        for k, v in crm_user_ids.items():
            if v > ov:
                ov = v
                _crm_user_id = k
        # pega o gerente_id que tem mais
        ov = -1
        for k, v in gerente_ids.items():
            if v > ov:
                ov = v
                _users_accounts_1users_ida = k
        # pega o master_id que tem mais
        ov = -1
        for k, v in parent_ids.items():
            if v > ov:
                ov = v
                _master_id = k

    # se a crm_user_id ou o userid forem informados, troca o representante 
    if userid or crm_user_id:
        if userid:
            user = dal_lm.GetUser(userid)
            crm_user = dal_crm.User_Get(CRM, email=user['email']) if user else None
            _crm_user_id = crm_user.get('id') if crm_user else None
            if not _crm_user_id:
                logger.critical(f"User não encontrado no SuiteCRM u:{user}")
        if not _crm_user_id:
            _crm_user_id = crm_user_id

    # se o _crm_user_id é vazio (não encontrou ninguém), coloca o WATSON
    if not _crm_user_id:
        _crm_user_id = WATSON_UserID

    # trata os Clientes (Autorizadores) associados à conta
    lista_contatos = ""
    autorizadores = dal_lm.GetAutorizadores(account_id)
    if autorizadores:
        for autorizador in autorizadores:
            # verifica se autorizador está no CRM
            crm_contatos = dal_crm.Contact_Get(CRM, name=autorizador['name'], email=autorizador['email'], document=autorizador['document'], phone=autorizador['phone'], mobile_phone=autorizador['mobile_phone'])
            if crm_contatos:
                _crm_contato = crm_contatos[0]
            else:
                _crm_contato = None

            contato_id = None
            # cria o contato ?
            if not _crm_contato:
                __autorizador = mod_crm.Contact().fromBO(autorizador).__dict__
                s, crm_contato = dal_crm.Contact_Create(CRM, __autorizador)
                if s:
                    logger.info(f"Erro:{s} ao criar o contato. Dados:{__autorizador}")
                else:
                    contato_id = crm_contato.get('id')
            else:
                contato_id = _crm_contato.get('id')
                _contato = mod_crm.Contact().fromBO(autorizador).__dict__
                _tipo_autorizador = _crm_contato.get("tipocontato_c",[])
                if '^Usuariobackoffice^' in _tipo_autorizador:
                    _tipo_autorizador.remove('^Usuariobackoffice^')
                if '^Autorizador^' in _tipo_autorizador:
                    _tipo_autorizador.remove('^Autorizador^')
                # ajustes legados - inicio
                if 'Usuariobackoffice' in _tipo_autorizador:
                    _tipo_autorizador.remove('Usuariobackoffice')
                if 'Autorizador' in _tipo_autorizador:
                    _tipo_autorizador.remove('Autorizador')
                # ajustes legados - fim
                for lm_tipoautorizador in _contato.get("tipocontato_c",[]):
                    if lm_tipoautorizador not in _tipo_autorizador:
                        _tipo_autorizador.extend([lm_tipoautorizador])
                _contato["tipocontato_c"] = _tipo_autorizador
                _contato['id'] = contato_id
                s, _ = dal_crm.Contact_Update(CRM, _contato)
                if s:
                    logger.debug(f"Erro:{s} ao atualizar o contato:{_contato['id']}. Dados:{_contato}")
            if contato_id:
                lista_contatos += f"{contato_id},"

    lm_bus = dal_lm.GetAccountBUs(account_id)
    for budata in lm_bus if lm_bus else []:
        suite_id = budata.get('suite_id')
        bu_id = budata.get('id')
        id_cliente = budata.get('id_cliente')

        for k, v in enumerate(crm_accounts): 
            if v.get('id') == suite_id: 
                del crm_accounts[k]
                break
        account_data = mod_crm.Account.fromBO(budata).__dict__
        account_data['assigned_user_id'] = _crm_user_id
        
        if gerente_relacionamento:
            account_data['gerente_relacionamento_name'] = gerente_relacionamento
        else:
            if _users_accounts_1users_ida:
                account_data['users_accounts_1users_ida'] = _users_accounts_1users_ida

        if _master_id:
            account_data['parent_id'] = _master_id

        respostas[bu_id] = ""
        suite_ids[bu_id] = suite_id

        if account_data['atividade_principal_c'] == 'Negocios':
            respostas[bu_id] = "Rever atividade Principal"
            suite_ids[bu_id] = None
            continue

        # está no CRM ?
        if suite_id:
            _crmdata = dal_crm.Account_Get(CRM, id=suite_id)
            if len(_crmdata) > 0:
                crmdata = _crmdata[0]
                account_data['assigned_user_id'] = _crm_user_id
                
                # se inativo no BO, remove do CRM
                if budata.get('status') != 0:
                    # verifica sem tem mais bu_id ou id_cliente nas listas
                    account_data['list_bu_id_c'] = crmdata.get('list_bu_id_c','').replace(f"{bu_id},",'')
                    account_data['list_id_cliente_c'] = crmdata.get('list_id_cliente_c','').replace(f"{id_cliente},",'')
                    # remove do CRM se listas vazias
                    dal_lm.PutSuiteID(bu_id, '') # marca no BO que saiu
                    if len(account_data['list_bu_id_c']) == 0 and len(account_data['list_id_cliente_c']) == 0:
                        removeu = dal_crm.Account_Delete(CRM, suite_id)
                        if removeu:
                            respostas[bu_id] += 'Removido CRM, inativo.'
                        else:
                            respostas[bu_id] += 'Tentativa de remoção do CRM.'
                        suite_ids[bu_id] = None
                        break
                    else:
                        # verifica se existe master conhecido, senão passa a ser este
                        if not _master_id:
                            _master_id = suite_id
                        account_data['parent_id'] = _master_id
                        # atualiza !
                        erro, data = dal_crm.Account_Update(CRM, account_data)
                        atualizou = erro is None
                        respostas[bu_id] += 'Removido da lista interna do CRM por inativo' if atualizou else 'Erro ao remover da lista.'
                        suite_ids[bu_id] = None
                        break

                # verifica se o bu_id está na lista
                if f"{bu_id}," not in crmdata.get('list_bu_id_c'):
                    account_data['list_bu_id_c'] = f"{crmdata.get('list_bu_id_c')}{bu_id},"
                if  f"{id_cliente}," not in crmdata.get('list_id_cliente_c'):
                    account_data['list_id_cliente_c'] = f"{crmdata.get('list_id_cliente_c')}{id_cliente},"

                # verifica se existe master conhecido, senão passa a ser este
                if not _master_id:
                    _master_id = suite_id
                account_data['parent_id'] = _master_id

                # atualiza !
                erro, data = dal_crm.Account_Update(CRM, account_data)
                atualizou = erro is None
                respostas[bu_id] += 'Atualizado.' if atualizou else 'Erro ao atualizar.'
            else:
                # estranho não achar no CRM pois tinha suite_id, marca para criar
                suite_id = None
                suite_ids[bu_id] = None
                account_data['id'] = None

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
                        
                        # atualiza o suite_id no BO
                        account_data['id'] = suite_id
                        dal_lm.PutSuiteID(bu_id, suite_id)
                        suite_ids[bu_id] = suite_id

                        # como achou por endereço, atualiza a lista de id_cliente e bu_id do suite_id
                        # pois mais de um registro no BO aponta para o mesmo suite_id
                        if f"{bu_id}," not in _acc.get('list_bu_id_c'):
                            account_data['list_bu_id_c'] = f"{_acc.get('list_bu_id_c')}{bu_id},"
                        if f"{id_cliente}," not in _acc.get('list_id_cliente_c'):
                            account_data['list_id_cliente_c'] = f"{_acc.get('list_id_cliente_c')}{id_cliente},"

                        # informa que foi processado
                        for k, v in enumerate(crm_accounts): 
                            if v.get('bu_id_c') == str(bu_id): 
                                del crm_accounts[k]
                                break

                        break
            else:
                respostas[bu_id] = 'Não sincronizado, sem endereço no BO.'
                continue

            # verifica se existe master conhecido, senão passa a ser este
            if not _master_id:
                _master_id = suite_id
            account_data['parent_id'] = _master_id                

            if suite_id:
                erro, data = dal_crm.Account_Update(CRM, account_data)
                atualizou = erro is None
                respostas[bu_id] += 'Atualizado.' if atualizou else 'Erro ao atualizar.'
            else:    
                # cria no CRM
                account_data['list_bu_id_c'] = str(bu_id) + ','
                account_data['list_id_cliente_c'] = str(id_cliente) + ',' 
                _, crm_account = dal_crm.Account_Create(CRM, account_data)
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

    # sobrou account ? Remover do CRM !!
    for _acc in crm_accounts:
        suite_id = _acc.get('id')
        if suite_id:
            # remove do CRM
            removeu = dal_crm.Account_Delete(CRM, suite_id)
            if removeu:
                if _acc.get('bu_id_c'):
                    bu_id = int(_acc.get('bu_id_c'))
                    suite_ids[bu_id] = suite_id
                    dal_lm.PutSuiteID(bu_id, '')
                    # pode ser que não esteja no vetor de respostas
                    try:
                        respostas[bu_id] += 'Removido CRM, inativo.'
                    except:
                        respostas[bu_id] = 'Removido CRM, inativo.'
            else:
                logger.critical(f"Erro na remoção do Account: {suite_id} .")
        else:
            logger.critical(f"Account: {suite_id} sem suite_id !")

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
                        if status:
                            logger.debug(f"Erro:{status} critico ao pegar o contato")
                            continue
                        contato_id = None
                        if contato and len(contato.get('data',[])) == 0:
                            __contato_data = mod_crm.Contact().fromBO(autorizador).__dict__
                            s, contato = dal_crm.Cria_contato(CRM, __contato_data)
                            if s:
                                logger.debug(f"Erro:{s} ao criar o contato. Dados:{__contato_data}")
                            else:
                                contato_id = contato['id']
                        else:
                            contato_id = contato[0]['id']                    
                        if contato_id:
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


def sync_BOContas_comLM(id_conta_lm:str=None) -> list:
    # não pode ser usada
    # só serve para criar
    return list()
    suite_ids = list()
    CRM = SuiteCRM.SuiteCRM(logger)
    BOContas = dal_lm.GetBOContas(id_conta_lm)
    # 393739
    #ww = CRM.GetData("GCR_ContaBackoffice", { 'id': '26c5bfb9-049a-f601-d309-6668336f5735' })
    for BOConta in BOContas:
        BOConta_data = mod_crm.BOConta().fromBO(BOConta).__dict__
        s, crm = CRM.PostData("GCR_ContaBackoffice", BOConta_data)
        if not s and crm:
            for acc_id in BOConta['crm_accounts'].split(','):
                r = CRM.AssociateData("GCR_ContaBackoffice", base_record_id=crm['id'], relate_module="accounts", relate_record_ids=acc_id)
                if not r:
                    print(crm['id'], acc_id)
                else:
                    suite_ids.append(crm.get('id'))                    
        print('id_conta_lm', BOConta['id_conta_lm'])                
    return suite_ids

def sync_BOContas_Accounts() -> None:
    CRM = SuiteCRM.SuiteCRM(logger)

    # pega todas as BOAccounts
    s, BOContas = dal_crm.Get(CRM, module="GCR_ContaBackoffice", filtro=dict())
    if s:
        for BOConta in BOContas.get('data',[]):
            BO_account_id = BOConta['id']
            # pega todas as contas com o mesmo id_conta_lm
            crm_accounts = dal_crm.Account_Get(CRM,account_id=BOConta.get('id_conta_lm'))

            # e associa ao BOAccount
            for crm_account in crm_accounts:
                acc_id = crm_account['id']
                _ = CRM.AssociateData("GCR_ContaBackoffice", base_record_id=BO_account_id, relate_module="accounts", relate_record_ids=acc_id)
                print('.', end='')
    print()


def sync_BOContas_Contracts() -> None:
    CRM = SuiteCRM.SuiteCRM(logger)

    idLM_Contracts = dal_lm.GetCRMIdContaLM_Contracts()
    for idLM_Contract in idLM_Contracts:
        s, BOConta = dal_crm.Get(CRM, module="GCR_ContaBackoffice", filtro={'id_conta_lm':idLM_Contract['id_conta_lm_c']})
        if s and BOConta and len(BOConta.get('data',[])) > 0:
            BOConta_id = BOConta['data'][0]['id']
            for crm_contract_id in idLM_Contract['contract_id_list'].split(','):
                _ = CRM.AssociateData("GCR_ContaBackoffice", base_record_id=BOConta_id, relate_module="contracts", relate_record_ids=crm_contract_id)
                print('.', end='')
    print()

def sync_BOContas_Contacts() -> None:
    CRM = SuiteCRM.SuiteCRM(logger)

    idLM_Contacts = dal_lm.GetCRMIdContaLM_Contacts()
    for idLM_Contact in idLM_Contacts:
        s, BOConta = dal_crm.Get(CRM, module="GCR_ContaBackoffice", filtro={'id_conta_lm':idLM_Contact['id_conta_lm']})
        if s and BOConta and len(BOConta.get('data',[])) > 0:
            BOConta_id = BOConta['data'][0]['id']
            for crm_contact_id in idLM_Contact['contact_id_list'].split(','):
                _ = CRM.AssociateData("GCR_ContaBackoffice", base_record_id=BOConta_id, relate_module="contacts", relate_record_ids=crm_contact_id)
                print('.', end='')
    print()



def trata_contatos(CRM, suite_id:str, contatos:list=list()) -> dict:
    def GetContato(k):
        __name = k.get('nome') if k.get('nome') else k.get('name')
        __name = re.sub('[^a-zA-Z0-9]', '', __name) if __name else ''
        __email = k.get('email')
        __document = re.sub('[^0-9]', '', k.get('document')) if k.get('document') else ''
        __phone = SuiteCRM.format_phone(k.get('phone'), internacional=True)
        __mobile_phone = SuiteCRM.format_phone(k.get('mobile_phone'), internacional=True)
        # verifica se autorizador está no CRM
        return dal_crm.Contact_Get(CRM, name=__name, email=__email, document=__document, phone=__phone, mobile_phone=__mobile_phone)

    lista_contatos:str = ''
    for contato in contatos:
        # verifica se o contato existe
        crm_contato = GetContato(CRM, contato)
        if crm_contato:
            contato['id'] = crm_contato.get('id')
            s, r = dal_crm.Contact_Update(CRM, contato)
            if s:
                logger.debug(f"Erro:{s} ao atualizar o contato {contato['id']} dados:{contato}")
            else:
                lista_contatos += f"{contato['id']},"
        else:
            s, r = dal_crm.Contact_Create(CRM, contato)
            if s:
                logger.debug(f"Erro:{s} ao criar contato, dados:{contato}")
            else:
                lista_contatos += f"{r.get('id')},"
    dal_crm.Associa_contatos(CRM, suite_id, lista_contatos[:-1])
    

def trata_contratos(CRM, suite_id:str, contratos) -> None:
    def GetContrato(k):
        __name = k.get('numero') if k.get('numero') else k.get('name')
        # verifica se está no CRM
        crm_contratos = dal_crm.Contract_Get(CRM, name=__name)
        _crm_contrato = None
        if crm_contratos:
            if len(crm_contratos) == 1:
                _crm_contrato = crm_contratos[0]
            else:
                logger.critical(f"Mais de um contrato com o reference_code:{__name}")    
        else:
            logger.info(f"Contrato com o reference_code:{__name} não foi encontrado.")    
        return _crm_contrato

    lista_contratos:str = ''
    for contrato in contratos:
        # verifica se o contato existe
        crm_contato = GetContrato(CRM, contrato)
        if crm_contato:
            contrato['id'] = crm_contato.get('id')
            s, r = dal_crm.Contract_Update(CRM, contrato)
            if s:
                logger.debug(f"Contrato com o id:{contrato['id']} não foi atualizado.")    
            else:
                lista_contratos += f"{contrato['id']},"
        else:
            s, r = dal_crm.Contract_Create(CRM, contrato)
            if s:
                logger.debug(f"Contrato com o reference_code:{contrato['reference_code']} não foi criado")    
            else:
                lista_contratos += f"{r.get('id')},"

    dal_crm.Associa_contratos(CRM, suite_id, lista_contratos[:-1])
        


def _infosComuns(CRM, suite_id:str, entity_data:dict):
    representante_comercial = entity_data.get("assigned_user_id")
    gerente_relacionamento = entity_data.get("users_accounts_1users_ida")
    conta_mestre = entity_data.get("parent_id")
    s, r = dal_crm.Get(CRM, module="accounts", filtro={'id': suite_id})
    id_conta_lm = r.get('data',[{}])[0].get("id_conta_lm_c",'0') if r else '0'
    # se informou o Representante Comercial ou o Gerente de Relacionamento e uma conta Mestre
    if id_conta_lm != '0':
        _dados = dict()
        if representante_comercial:
            _dados["assigned_user_id"] = representante_comercial
        if gerente_relacionamento:
            _dados["users_accounts_1users_ida"] = gerente_relacionamento
        if conta_mestre:
            _dados["parent_id"] = conta_mestre
        if _dados:
            # força todas as crm_contas a ter o mesmo Representante e/ou Gerente
            for conta in dal_crm.Account_Get(CRM, account_id=id_conta_lm):
                _dados["id"] = conta.get('id')
                if _dados["id"] != suite_id:
                    _s, _d = dal_crm.Put(CRM, module="accounts", entity_data=_dados)
                    if _s:
                        logger.debug(f"Erro:{_s}, Conta:{_dados['id']} não foi atualizada")    
                        

def Get(module:str, filtro:dict=dict()) -> tuple[bool, dict]:
    if module == 'conta':
        module = 'accounts'
        if not filtro.get('id_cliente') and not filtro.get('id_cliente_c') and not filtro.get('id'):
            return False, { 'msg':'O ID do Cliente não foi informado [id_cliente].' }
    elif module == 'contato':
        module = 'contacts'
        if not filtro.get('nome') and not filtro.get('name') and not filtro.get('email') and not filtro.get('first_name') and not filtro.get('id'):
            return False, { 'msg':'Os filtros possíveis são [nome], [email], [first_name] e [id].' }

    CRM = SuiteCRM.SuiteCRM(logger)
    return dal_crm.Get(CRM, module=module, filtro=filtro)


def Put(module:str, entity_data:dict) -> tuple[bool, dict]:
    CRM = SuiteCRM.SuiteCRM(logger)
    if module in ['conta']:
        module = 'accounts'
        id_cliente = entity_data.get('id_cliente')
        if id_cliente:
            del entity_data['id_cliente']
            s, d = dal_crm.Get(CRM, module, filtro={'id_cliente_c': id_cliente})
            if s:
                data = d.get('data',[])
                if len(data) == 1:
                    entity_data['id'] = data[0].get('id')
                else:
                    return False, { 'msg':'O Cliente não foi encontrado.' }
        else:
            return False, { 'msg':'O ID do Cliente não foi informado [id_cliente].' }
        contatos = entity_data.get('CONTATOS')
        if contatos:
            entity_data.remove('CONTATOS')
        contratos = entity_data.get('CONTRATOS')
        if contratos:
            entity_data.remove('CONTRATOS')

    elif module == 'contato':
        module = 'contacts'
        if not entity_data.get('id'):
            return False, { 'msg':'O ID do contato precisa ser informado [id].' }

    s, d = dal_crm.Put(CRM, module=module, entity_data=entity_data)
    suite_id = d.get('data',{}).get('id') if d else None
    if suite_id and module == 'accounts':
        # trata as informações que devem ser as mesmas para todas as contas com o mesmo id_conta_lm_
        _infosComuns(CRM, suite_id, entity_data)
        if contatos: trata_contatos(CRM, suite_id, contatos)
        if contratos: trata_contratos(CRM, suite_id, contratos)
    return s, d


def Post(module:str, entity_data:dict) -> tuple[bool, dict]:
    if module in ['conta']:
        module = 'accounts'
        id_cliente = entity_data.get('id_cliente')
        if id_cliente:
            del entity_data['id_cliente']
            entity_data['id_cliente_c'] = id_cliente
    elif module == 'contato':
        module = 'contacts'
        if not entity_data.get('id_cliente') and not entity_data.get('id_cliente_c'):
            return False, { 'msg':'Falta indicação da Conta associada a esse Contato [id_cliente].' }
        
    CRM = SuiteCRM.SuiteCRM(logger)
    s, d = dal_crm.Post(CRM, module=module, entity_data=entity_data)
    suite_id = d.get('data',{}).get('id') if d else None
    if suite_id and module == 'accounts':
        # trata as informações que devem ser as mesmas para todas as contas com o mesmo id_conta_lm_
        _infosComuns(CRM, suite_id, entity_data)
    return s, d


def Delete(module:str, entity_data:dict) -> bool:
    CRM = SuiteCRM.SuiteCRM(logger)
    return dal_crm.Delete(CRM, module=module, entity_data=entity_data)


def processa_arquivo_contas(file_path:str, skiplines:int=0):
    inclusoes = 0
    atualizacoes = 0
    sem_ids = 0
    formatacao = 0
    file_path = "/mnt/shared/crm/" + file_path
    CRM = SuiteCRM.SuiteCRM(logger) 

    # Open the CSV file in read mode
    with open(file_path, 'r') as file:
        # Create a CSV reader object
        csv_reader = csv.reader(file)

        # Loop through each row in the CSV file
        row_num = 0
        for row in csv_reader:
            row_num += 1
            if row_num == 1:
                headers = row
                headers[0] = headers[0].replace('\ufeff', '').replace('"','')
                logger.info(f"Header carregado:{headers}")
            else:
                if row_num >= skiplines:
                    print(row_num)
                    dado = row
                    if len(dado) != len(headers):
                        logger.info(f"linha:{row_num} - Quantidade de campos:{len(dado)} desta linha difere do header:{len(headers)}")
                        formatacao += 1
                        continue

                    account_data = dict()
                    for i in range(len(headers)):
                        if headers[i] == 'assigned_user_name':
                            account_data[headers[i]] = dado[i].upper()
                        else:    
                            account_data[headers[i]] = dado[i]

                    # Só processa que tem o 'link' completo
                    if not (account_data.get('id_conta_lm_c') \
                            # and account_data.get('bu_id_c') \
                            and (account_data.get('id_cliente_c') or account_data.get('id_cliente')) ) :
                        logger.info(f"linha:{row_num} - Falta informação no CSV: id_conta_lm:{account_data.get('id_conta_lm_c')}, buid:{account_data.get('bu_id_c')}, id_cliente:{account_data.get('id_cliente_c')}")
                        sem_ids += 1
                        continue

                    # pega o id_cliente
                    if (_idc1:=account_data.get('id_cliente_c')) or (_idc2:=account_data.get('id_cliente')):
                        _id_cliente = _idc1 if _idc1 else _idc2

                    # é para deletar ?
                    if account_data.get('status') == 'D':
                        crm_accounts = dal_crm.Account_Get(CRM, id_cliente=_id_cliente)
                        if crm_accounts and len(crm_accounts) >= 1:
                            if len(crm_accounts) == 1:
                                # deleta a conta
                                deletou = dal_crm.Account_Delete(CRM, crm_accounts[0]['id'])
                                if deletou:
                                    logger.info(f"linha:{row_num} - Account {crm_accounts[0]['id']} deletado do CRM.")
                                else:
                                    logger.critical(f"linha:{row_num} - Problemas pata deletar o account {crm_accounts[0]['id']}")
                            elif len(crm_accounts) > 1:
                                logger.critical(f"linha:{row_num} - Multiplas contas com id_cliente:{_id_cliente}")
                            else:
                                logger.critical(f"linha:{row_num} - Conta com id_cliente:{_id_cliente} não localizado no CRM !")
                        continue
                    continue
                    # pega todas as contas com o mesmo id_conta_lm
                    contas_mesmo_id_conta_lm = dal_crm.Account_Get(CRM, account_id=account_data.get('id_conta_lm_c'))

                    # conta existe ?
                    crm_accounts = dal_crm.Account_Get(CRM, account_id=account_data.get('id_conta_lm_c'), buid=account_data.get('bu_id_c'), id_cliente=_id_cliente)
                    if crm_accounts and len(crm_accounts) >= 1:
                        if len(crm_accounts) == 1:
                            # indica o ID para atualizar
                            account_data['id'] = crm_accounts[0].get('id')
                            s, crm_account = dal_crm.Account_Update(CRM, account_data )
                            if s:
                                logger.info(f"linha:{row_num} - Conta:{account_data['id']} não foi atualizada. Erro:{s}.")
                            else:
                                atualizacoes += 1
                                dal_lm.PutSuiteID(crm_account.get('bu_id_c'), crm_account.get('id'))
                        else:
                            logger.critical(f"linha:{row_num} - Multiplas contas com essa chave: id_conta_lm:{account_data.get('id_conta_lm_c')}, bu_id:{account_data.get('bu_id_c')}, id_cliente:{account_data.get('id_cliente_c')}")
                            s = "ERRO - MULTIPLAS CONTAS"
                            r = None
                    else:
                        # conta não existe no CRM
                        if contas_mesmo_id_conta_lm and len(contas_mesmo_id_conta_lm) > 0:
                            account_data['parent_id'] = contas_mesmo_id_conta_lm[0].get('parent_id')
                        s, crm_account = dal_crm.Account_Create(CRM, account_data)
                        # se criou e existe, acertar o 'link' no BO
                        if s:
                            logger.info(f"linha:{row_num} - Conta não foi criada. Erro:{s}, Dados:{account_data}")
                        else:
                            dal_lm.PutSuiteID(crm_account.get('bu_id_c'), crm_account.get('id'))
                            inclusoes += 1
                    # se a inclusão/atualizaçãofuncionou ...
                    if not s:
                        # BOAccounts existe ?
                        BOAccount = CRM.get_BOconta(id_conta_lm=crm_account['id_conta_lm_c'])
                        if not BOAccount:
                            # cria o BOAccount
                            s, BOAccount = CRM.cria_BOconta(name=crm_account.get('name'), 
                                                            id_conta_lm=crm_account.get('id_conta_lm_c'), 
                                                            assigned_user_id=crm_account.get('assigned_user_id'), 
                                                            gerente_relacionamento_id=crm_account.get('users_accounts_1users_ida'), 
                                                            account_ids=crm_account['id'] )
                        else:
                            # testa se alterou o RC ou o GC
                            atualizaRC = BOAccount[0].get('assigned_user_id') != crm_account.get('assigned_user_id')
                            atualizaGC = BOAccount[0].get('users_gcr_contabackoffice_1users_ida') != crm_account.get('users_accounts_1users_ida')
                            if atualizaRC or atualizaGC:
                                s, _ = dal_crm.ContaBO_Update(CRM, {'id':BOAccount[0]['id'], 
                                                                    'assigned_user_id': crm_account.get('assigned_user_id'), 
                                                                    'gerente_relacionamento_id': crm_account.get('users_accounts_1users_ida'), 
                                                                    'account_ids': crm_account['id']} )
                                # acerta o gerente e o representante nas outras contas com o mesmo id_conta_lm
                                if contas_mesmo_id_conta_lm and len(contas_mesmo_id_conta_lm) > 0:
                                    for conta_mesmo_id_conta_lm in contas_mesmo_id_conta_lm:
                                        if atualizaGC:
                                            dal_crm.Account_RemoveGrupoSeguranca(CRM, conta_mesmo_id_conta_lm.get('id'), conta_mesmo_id_conta_lm.get('users_accounts_1_name',{}).get('name'))
                                        # não atualiza o que já foi atualizado
                                        if crm_account.get('id') != conta_mesmo_id_conta_lm.get('id'):
                                            dal_crm.Account_Update(CRM, { 
                                                                          'id': conta_mesmo_id_conta_lm.get('id'),
                                                                          'users_accounts_1users_ida': crm_account.get('users_accounts_1users_ida'),
                                                                          'assigned_user_id': crm_account.get('assigned_user_id')
                                                                        } 
                                                                   )
                            else:
                                # só inclui
                                _ = CRM.AssociateData("GCR_ContaBackoffice", base_record_id=BOAccount[0]['id'], relate_module="accounts", relate_record_ids=crm_account['id'])
                if row_num % 50 == 0:
                    logger.info(f"Processados {row_num} registros, Incluidos:{inclusoes} Atualizados:{atualizacoes} Sem IDS:{sem_ids} Formatação incorreta:{formatacao}")
    logger.info(f"Fim do processamento.{CRLF}{TAB}Processados {row_num} registros:{CRLF}{TAB}{TAB}Incluidos:{inclusoes}{CRLF}{TAB}{TAB}Atualizados:{atualizacoes}{CRLF}{TAB}{TAB}Sem IDS:{sem_ids}{CRLF}{TAB}{TAB}Formatação incorreta:{formatacao}")
    return f"Processados {row_num} registros:{CRLF}{TAB}Incluidos:{inclusoes}{CRLF}{TAB}Atualizados:{atualizacoes}{CRLF}{TAB}Sem IDS:{sem_ids}{CRLF}{TAB}{TAB}Formatação incorreta:{formatacao}"


def processa_arquivo_contratos(file_path:str, skiplines:int=0) -> str:
    def check_date_format(data:str) -> str:
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if re.match(pattern, data):
            return 'INT'
        pattern = r'^\d{2}/\d{2}/\d{4}$'
        if re.match(pattern, data):
            return 'BRA'
        return '??'

    def conv_date(data) -> date:
        if data is None:
            return None
        if isinstance(data, date):
            return data
        if isinstance(data, datetime):
            return data.date()
        if check_date_format(data) == 'INT':
            return datetime.strptime(data, '%Y-%m-%d').date()
        if check_date_format(data) == 'BRA':
            return datetime.strptime(data, '%d/%m/%Y').date()
        return None

    inclusoes = 0
    atualizacoes = 0
    sem_ids = 0
    formatacao = 0
    file_path = "/mnt/shared/crm/" + file_path
    CRM = SuiteCRM.SuiteCRM(logger) 
    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)

        row_num = 0
        for row in csv_reader:
            row_num += 1      
            del row[22]
            del row[21]
            del row[17]
            del row[16]
            del row[15]
            del row[14]
            del row[13]
            del row[12]
            del row[7]
            del row[6]
            if row_num == 1:
                headers = row
                headers[0] = headers[0].replace('\ufeff', '').replace('"','')
                logger.info(f"Header carregado:{headers}")
            else:
                if row_num >= skiplines:
                    dado = row
                    if len(dado) != len(headers):
                        logger.info(f"linha:{row_num} - Quantidade de campos:{len(dado)} desta linha difere do header:{len(headers)}")
                        formatacao += 1
                        continue
                    
                    contract_data = dict()
                    for i in range(len(headers)):
                        if headers[i] in ["date_entered","start_date","end_date","customer_signed_date","company_signed_date","renewal_reminder_date","data_cancelamento_c"]:
                            contract_data[headers[i]] = conv_date(dado[i])
                        elif headers[i] in ["total_contract_value"]:
                            if dado[i].startswith('R$'):
                                contract_data[headers[i]] = dado[i].replace('R$','').replace('.','').replace(',','.')
                            else:
                                contract_data[headers[i]] = dado[i]
                        else:
                            contract_data[headers[i]] = dado[i]
                    
                    # informou o número do contrato ?
                    if (_reference_code:=contract_data.get('reference_code')):
                        contract_data['name'] = _reference_code
                    else:
                        logger.debug(f"linha:{row_num} - Número do contrato [reference_code] não informada.")
                        continue

                    contract_data['status'] = 'Signed'
                    if contract_data.get('data_cancelamento_c') and not contract_data.get('end_date'):
                        contract_data['end_date'] = contract_data.get('data_cancelamento_c')
                    print(contract_data.get('data_cancelamento_c'), contract_data.get('ativo_c'))

                    # informou a conta ?
                    if (_id_cli1:=contract_data.get('id_cliente')) or (_id_cli2:=contract_data.get('id_cliente_c')):
                        crm_account = dal_crm.Account_Get(CRM, id_cliente=_id_cli1 if _id_cli1 else _id_cli2)
                    else:
                        logger.debug(f"linha:{row_num} - Conta [id_cliente] não informada.")
                        continue

                    # se a conta existe ...
                    if crm_account:
                        # coloca o id da conta nos dados
                        contract_data['contract_account_id'] = crm_account[0].get('id')

                        # verifica se o contrato existe
                        crm_contrato = dal_crm.Contract_Get(CRM, name=contract_data['name'])
                        if crm_contrato:
                            contract_data['id'] = crm_contrato[0].get('id')
                            s, k = dal_crm.Contract_Update(CRM, contract_data)
                            if s:
                                logger.debug(f"linha:{row_num} - Erro:{s}, Contrato:{contract_data.get('id')} não foi atualizado. Dados:{contract_data}")
                            else:
                                atualizacoes += 1
                        else:
                            s, k = dal_crm.Contract_Create(CRM, contract_data)
                            if s:
                                logger.debug(f"linha:{row_num} - Erro:{s}, Contrato não foi criado. Dados:{contract_data}")
                            else:
                                inclusoes += 1
                    else:
                        logger.debug(f"linha:{row_num} - Conta id_cliente:{contract_data.get('id_cliente')} não existe no CRM")
                        sem_ids += 1
            if (row_num % 50) == 0:
                logger.info(f"Processados {row_num} registros, Incluidos:{inclusoes} Atualizados:{atualizacoes} Sem IDS:{sem_ids}")
    logger.info(f"Fim do processamento.{CRLF}{TAB}Processados {row_num} registros:{CRLF}{TAB}{TAB}Incluidos:{inclusoes}{CRLF}{TAB}{TAB}Atualizados:{atualizacoes}{CRLF}{TAB}{TAB}Sem IDS:{sem_ids}")
    return f"Processados {row_num} registros:{CRLF}{TAB}Incluidos:{inclusoes}{CRLF}{TAB}Atualizados:{atualizacoes}{CRLF}{TAB}Sem IDS:{sem_ids}"


def processa_arquivo_contatos(file_path:str, skiplines:int=0) -> str:
    inclusoes = 0
    atualizacoes = 0
    sem_ids = 0
    formatacao = 0
    file_path = "/mnt/shared/crm/" + file_path
    CRM = SuiteCRM.SuiteCRM(logger) 
    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)

        row_num = 0
        deletar = -1
        for row in csv_reader:
            row_num += 1
            if row_num == 1:
                headers = row
                headers[0] = headers[0].replace('\ufeff', '').replace('"','')
                for i in range(len(headers)):
                    if headers[i] == "titel":
                        headers[i] = "title"
                    if headers[i] == "account_name":
                        deletar = i
                if deletar > 0:
                    del headers[deletar]
                    
                logger.info(f"Header carregado:{headers}")
            else:
                if row_num >= skiplines:
                    dado = row
                    if deletar > 0:
                        del dado[deletar]

                    if len(dado) != len(headers):
                        logger.info(f"linha:{row_num} - Quantidade de campos:{len(dado)} desta linha difere do header:{len(headers)}")
                        formatacao += 1
                        continue

                    contact_data = dict()
                    for i in range(len(headers)):
                        contact_data[headers[i]] = dado[i]

                    if (_street:=contact_data.get('primary_address_street')):
                        contact_data['primary_address_street'] = re.sub(' +', ' ', _street)

                    # verifica se a conta existe
                    if (_idc1:=contact_data.get('id_cliente')) or (_idc2:=contact_data.get('id_cliente_c')):
                        _id_cliente = _idc1 if _idc1 else _idc2
                        crm_account = dal_crm.Account_Get(CRM, id_cliente=_id_cliente)
                    else:
                        _id_cliente = None
                        logger.info(f"linha:{row_num} - Cliente [id_cliente] não informado")
                        continue

                    # se a conta existe, trata o Contato
                    if crm_account:
                        if len(crm_account) == 1:
                            #pega todas as contas com o mesmo id_conta_lm
                            contas_mesmo_id_conta_lm = dal_crm.Account_Get(CRM, account_id=crm_account[0].get('id_conta_lm_c'))

                            crm_contato = dal_crm.Contact_Get(CRM, name=contact_data.get('first_name'), 
                                                                   email=contact_data.get('email1'), 
                                                                   document=contact_data.get('cpf_c'), 
                                                                   phone=contact_data.get('phone_work'),
                                                                   mobile_phone=contact_data.get('phone_mobile'),
                                                                   whatsapp=contact_data.get('phone_mobile')
                                                                )
                            contact_data['contact_account_id'] = crm_account[0].get('id')
                            if crm_contato:
                                crm_contato_id = crm_contato.get('id')
                                contact_data['id'] = crm_account[0].get('id')
                                s, k = dal_crm.Contact_Update(CRM, contact_data)
                                if s:
                                    logger.debug(f"linha:{row_num} - Erro:{s}, Contato:{contact_data['id']} não foi atualizado. Dados:{contact_data}")
                                    continue
                                else:
                                    atualizacoes += 1
                            else:
                                s, k = dal_crm.Contact_Create(CRM, contact_data)
                                if s:
                                    logger.debug(f"linha:{row_num} - Erro:{s}, Contato não foi criado. Dados:{contact_data}")
                                else:
                                    inclusoes += 1
                                    crm_contato_id = k.get('id')
                            # se incluiu / atualizou
                            if k:
                                # associa o contato as outras contas com o mesmo id_lm
                                for conta_mesmo_id_conta_lm in contas_mesmo_id_conta_lm:
                                    r = dal_crm.Associa_contatos(CRM, conta_mesmo_id_conta_lm.get('id'), str(crm_contato_id))
                                    if not r:
                                        logger.debug(f"Associação da conta {conta_mesmo_id_conta_lm.get('id')} com o contato {k.get('id')}com problemas")
                        else:
                            logger.debug(f"linha:{row_num} - Multiplas contas com esse id_cliente:{_id_cliente}")
                            sem_ids += 1
                    else:
                        logger.debug(f"linha:{row_num} - Conta id_cliente:{_id_cliente} não existe no CRM")
                        sem_ids += 1
                if row_num % 50 == 0:
                    logger.info(f"Processados {row_num} registros, Incluidos:{inclusoes} Atualizados:{atualizacoes} Sem IDS:{sem_ids}")
    logger.info(f"Fim do processamento.{CRLF}{TAB}Processados {row_num} registros:{CRLF}{TAB}{TAB}Incluidos:{inclusoes}{CRLF}{TAB}{TAB}Atualizados:{atualizacoes}{CRLF}{TAB}{TAB}Sem IDS:{sem_ids}")
    return f"Processados {row_num} registros:{CRLF}{TAB}Incluidos:{inclusoes}{CRLF}{TAB}Atualizados:{atualizacoes}{CRLF}{TAB}Sem IDS:{sem_ids}"


# sync_bo()
# sync_account(19825816) # bysdev

#w = sync_CRM2BO_Account()
#z = sync_BO2CRM_Account(510474)
#print(w)
            
#r = dict()
#x = sync_BO2CRM_Account('1778052', userid=10, gerente_relacionamento="Andre.Silveira")
#print(x)
#print() 

# cria_notificacao(business_unit_id=719825816, titulo="Site publicado !", texto="OK")



