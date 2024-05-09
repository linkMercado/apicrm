import re

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
            __name = re.sub('[^a-zA-Z0-9]', '', autorizador['name']) if autorizador.get('name') else ''
            __email = autorizador['email']
            __document = re.sub('[^0-9]', '', autorizador['document']) if autorizador.get('document') else ''
            __phone = SuiteCRM.format_phone(autorizador.get('phone'), internacional=True)
            __mobile_phone = SuiteCRM.format_phone(autorizador.get('mobile_phone'), internacional=True)

            # verifica se autorizador está no CRM
            crm_contatos = dal_crm.Contact_Get(CRM, name=autorizador['name'], email=autorizador['email'], document=autorizador['document'], phone=autorizador['phone'], mobile_phone=autorizador['mobile_phone'])

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
                    if nota > nota_maxima:
                        nota_maxima = nota
                        _crm_contato = crm_contato

            # cria o contato ?
            if not _crm_contato:
                _, crm_contato = dal_crm.Contact_Create(CRM, mod_crm.Contact().fromBO(autorizador).__dict__)
                contato_id = crm_contato.get('id')
                logger.info(f"Contato criado no SuiteCRM c:{autorizador}, id:{contato_id}")
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
                atualizou = dal_crm.Contact_Update(CRM, _contato)
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
                        atualizou = dal_crm.Account_Update(CRM, account_data)
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
                atualizou = dal_crm.Account_Update(CRM, account_data)
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
                atualizou = dal_crm.Account_Update(CRM, account_data)
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
                    if not _s:
                        print(_d)


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
    elif module == 'contato':
        module = 'contacts'
        if not entity_data.get('id'):
            return False, { 'msg':'O ID do contato precisa ser informado [id].' }

    s, d = dal_crm.Put(CRM, module=module, entity_data=entity_data)
    suite_id = d.get('data',{}).get('id') if d else None
    if suite_id and module == 'accounts':
        # trata as informações que devem ser as mesmas para todas as contas com o mesmo id_conta_lm_
        _infosComuns(CRM, suite_id, entity_data)
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



