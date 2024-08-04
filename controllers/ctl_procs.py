import re
import csv
import string

from datetime import date, datetime
from apicrm import LOGGER as logger
from apicrm import SUITECRM as SuiteCRM 
from lm_packages.Extras import TAB, CRLF

from models import mod_crm
from dal import dal_lm
from dal import dal_crm

WATSON_UserID = 'a2fc0fc9-cb48-39c3-2bb2-658b42a377d7'

def GetBOAccount(CRM:SuiteCRM.SuiteCRM, id:str=None, id_conta_lm:str=None) -> dict:
    if id:
        filtro = { 'id': id}
    elif id_conta_lm:
        filtro = { 'id_conta_lm': id_conta_lm}
    else:
        filtro = None
    if filtro:
        if not CRM:
            CRM = SuiteCRM.SuiteCRM(logger)
        resp = dal_crm.BOAccount_Get(CRM, filtro)
        resposta = list()
        for r in resp:
            if r['id_conta_lm'] != str(id_conta_lm):
                continue
            resposta.append(r)
        return resposta
    else:
        return dict()


def GetContact(CRM:SuiteCRM.SuiteCRM, id:str=None, fname:str=None, lname:str=None, email:str=None, document:str=None, phone_work:str=None, mobile_phone:str=None, whatsapp:str=None) -> list[dict]:
    if not CRM:
        CRM = SuiteCRM.SuiteCRM(logger)
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

        crm_contatos = dal_crm.Contact_Get(CRM, filtro=filtro)
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
        return list()


def GetAccount(CRM:SuiteCRM.SuiteCRM, id:str=None, id_conta_lm:str=None, buid:str=None, id_cliente:str=None, status:str=None) -> list[dict]:
    resposta = list()
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
    if filtro:
        if not CRM:
            CRM = SuiteCRM.SuiteCRM(logger)
        resp = dal_crm.Account_Get(CRM, filtro=filtro)
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


def GetContract(CRM:SuiteCRM.SuiteCRM, id:str=None, name:str=None, numero:str=None) -> list[dict]:
    filtro = dict()
    if id:
        filtro['id'] = id
    if name:
        filtro['name'] = name
    if numero:
        filtro['reference_code'] = numero
    if filtro:       
        if not CRM:
            CRM = SuiteCRM.SuiteCRM(logger)
        resp = dal_crm.Contract_Get(CRM, filtro=filtro)
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
        return list()


def sync_BO2CRM_Account(account_id:str, userid:str=None, crm_user_id:str=None, gerente_relacionamento:str=None) -> tuple[dict, dict]:
    return dict(), dict()
    """
      FORA DE USO
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
    crm_accounts = dal_crm.Account_Get(CRM, id=None, id_conta_lm=account_id)
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
            crm_contatos = dal_crm.Contact_Get(CRM, name=autorizador['name'], email=autorizador['email'], document=autorizador['document'], phone_work=autorizador['phone'], mobile_phone=autorizador['mobile_phone'])
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

    lm_bus = dal_lm.GetBUs(account_id)
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
                            respostas[bu_id] += 'Tentativa de remoção do CRM'
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
                for _acc in dal_crm.Account_Get(CRM, id=None, id_conta_lm=account_id):
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
            r = dal_crm.Account_AssociaContatos(CRM, suite_id, lista_contatos[:-1])
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
    """


def sync_BO2CRM_BUsBeneficiadas() -> tuple[dict, dict]:
    """
      Atualiza as BUs 'beneficiadas' no CRM
    """
    CRM = SuiteCRM.SuiteCRM(logger)     
    respostas:dict = dict()
    suite_ids:dict = dict()

    # pega o BOAccount
    BOAccounts = dal_crm.BOAccounts(CRM)
    for BOAccount in BOAccounts:
        BOAccount_id = BOAccount['id']
        id_conta_lm = BOAccount['id_conta_lm']

        # pega as BUs do BO com o id_conta_lm
        lm_bus = dal_lm.GetBUs(accountid=id_conta_lm)

        # compara as BUs do BO com as do CRM (cria e/ou atualiza)
        for budata in lm_bus if lm_bus else []:
            account_data = mod_crm.Account.fromBO(budata).__dict__
            if account_data['atividade_principal_c'] == 'Negocios':
                respostas[bu_id] = "Rever atividade Principal"
                suite_ids[bu_id] = None
                continue

            suite_id = budata.get('suite_id')
            bu_id = budata.get('bu_id')
            id_cliente = budata.get('id_cliente')
            contrato = budata.get('contract_number')
            contratoX = budata.get('contrato_expandido')

            # pega o Contrato que beneficia essa BU
            crm_contract = GetContract(CRM, numero=contrato)
            if not crm_contract or len(crm_contract) == 0:
                logger.critical(f"O Contrato {contrato} não está no CRM")
                continue
            else:
                crm_contract = crm_contract[0]

            respostas[bu_id] = ""
            suite_ids[bu_id] = suite_id
            
            # está no CRM ?
            crm_bu = GetAccount(CRM, buid=bu_id)
            if not crm_bu:
                # tentativa por endereço, dentro do mesmo id_conta_lm
                _endereco = re.sub('[^a-zA-Z0-9]', '', mod_crm.Account._endereco(budata.get('street_type'), budata.get('street'), budata.get('house_number'), budata.get('additional_address')))
                k, _k, _crm_bu = 0, 0, None
                crm_bus = GetAccount(CRM, id_conta_lm=id_conta_lm)
                for crm_bu in crm_bus if crm_bus else []:
                    if _endereco == re.sub('[^a-zA-Z0-9]', '', account_data['billing_address_street']):
                        k += 1
                    if bu_id == account_data['bu_id_c']:
                        k += 1
                    if k > _k:
                        _k = k
                        _crm_bu = crm_bu
            else:
                _crm_bu = crm_bu[0]

            # trata inativação (remoção) do CRM
            if account_data['status_c'] == 'Inativo':
                if _crm_bu:
                    suite_ids[bu_id] = None
                    # retira a marcação no BO
                    dal_lm.PutSuiteID(bu_id, '')

                    # verifica se é o único BU_ID desse Account
                    if (list_bu_ids:=_crm_bu.get('list_bu_ids_c')):
                        list_bu_ids = list_bu_ids.replace(f"{bu_id},",'') if list_bu_ids else ''
                    if list_bu_ids:
                        _crm_bu['list_bu_ids_c'] = list_bu_ids
                        s, _ = dal_crm.Account_Update(CRM, _crm_bu)
                        if s:
                            respostas[bu_id] += f"Tentativa de atualizar Account do CRM frustrada, id:{_crm_bu['id']}"
                        else:
                            respostas[bu_id] += 'Removido do CRM, inativo.'
                    else:
                        removeu = dal_crm.Account_Delete(CRM, crm_id=_crm_bu['id'])
                        if removeu:
                            respostas[bu_id] += 'Removido CRM, inativo.'
                        else:
                            respostas[bu_id] += f"Tentativa de remover Account do CRM frustrada, id:{_crm_bu['id']}"
                        continue

            # achou ?
            if not _crm_bu:
                # Bu Nova
                account_data['bu_id_c'] = bu_id
                account_data['list_bu_id_c'] = f"{bu_id},"
                account_data['id_cliente_c'] = None
                account_data['id_conta_lm_c'] = id_conta_lm
                s, _crm_bu = dal_crm.Account_Create(CRM, account_data)
                if s:
                    respostas[bu_id] = f"Não foi possivel criar a BU id_cliente/bu_id {id_cliente}/{bu_id}"
                    suite_ids[bu_id] = None
                    continue
                else:
                    respostas[bu_id] += 'Atualizado.'
                    suite_ids[bu_id] = suite_id
                    # atualiza a lista de bu_ids dessa BU
                    if f"{bu_id}," not in crm_bus.get('list_bu_id_c'):
                        account_data['list_bu_id_c'] = f"{crm_bus.get('list_bu_id_c')}{bu_id},"
                    dal_lm.PutSuiteID(bu_id, _crm_bu['id']) # marca no BO

            # faz as associações
            # 1 - BOAccount
            dal_crm.BOAccount_AssociaBU(CRM, crm_id=BOAccount_id, crm_account_ids=_crm_bu['id'])
            # 2 - Contract
            dal_crm.Contract_AssociaAccounts(CRM, crm_contract_id=crm_contract['id'], crm_account_id=_crm_bu['id'])

    # sobrou account ? Remover do CRM !!
    for _acc in crm_bus:
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
            logger.critical(f"Account: {suite_id} sem suite_id !")

    return respostas, suite_ids


def sync_CRM2BO_Account() -> tuple[str: dict]:
    msg_tec:str = ""
    suite_ids = dict()
    CRM = SuiteCRM.SuiteCRM(logger)

    crm_accounts = GetAccount(CRM, id=None)
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


def trata_contatos(CRM, suite_id:str, contatos:list=list()) -> dict:
    def GetContato(k):
        __name = k.get('nome') if k.get('nome') else k.get('name')
        __name = re.sub('[^a-zA-Z0-9]', '', __name) if __name else ''
        __email = k.get('email')
        __document = re.sub('[^0-9]', '', k.get('document')) if k.get('document') else ''
        __phone = SuiteCRM.format_phone(k.get('phone'), internacional=True)
        __mobile_phone = SuiteCRM.format_phone(k.get('mobile_phone'), internacional=True)
        # verifica se autorizador está no CRM
        return GetContact(CRM, name=__name, email=__email, document=__document, phone_work=__phone, mobile_phone=__mobile_phone)

    lista_contatos:str = ''
    for contato in contatos:
        # verifica se o contato existe
        crm_contato = GetContato(CRM, contato)
        if crm_contato:
            contato['id'] = crm_contato.get('id')
            s, r = dal_crm.Contact_Update(CRM, contato)
            if not s:
                lista_contatos += f"{contato['id']},"
        else:
            s, r = dal_crm.Contact_Create(CRM, contato)
            if not s:
                lista_contatos += f"{r.get('id')},"
    dal_crm.Account_AssociaContatos(CRM, suite_id, lista_contatos[:-1])
    

def trata_contratos(CRM, suite_id:str, contratos) -> None:
    def GetContrato(k):
        __numero = None
        __name = None
        if (__numero:=k.get('reference_code')):
            crm_contratos = GetContract(CRM, numero=__numero)
        elif (__name:=k.get('name')):
            crm_contratos = GetContract(CRM, name=__name)
        # verifica se está no CRM
        _crm_contrato = None
        if crm_contratos:
            if len(crm_contratos) == 1:
                _crm_contrato = crm_contratos[0]
            else:
                logger.critical(f"Mais de um contrato com o reference_code:{__numero} e/ou nome:{__name}")    
        else:
            logger.warning(f"Contrato com o reference_code:{__numero} e/ou nome:{__name}  não foi encontrado.")
        return _crm_contrato

    lista_contratos:str = ''
    for contrato in contratos:
        # verifica se o contato existe
        crm_contato = GetContrato(CRM, contrato)
        if crm_contato:
            contrato['id'] = crm_contato.get('id')
            s, r = dal_crm.Contract_Update(CRM, contrato)
            if not s:
                lista_contratos += f"{contrato['id']},"
        else:
            s, r = dal_crm.Contract_Create(CRM, contrato)
            if not s:
                lista_contratos += f"{r.get('id')},"

    dal_crm.Account_AssociaContracts(CRM, suite_id, lista_contratos[:-1])
        

def _infosComuns(CRM, suite_id:str, entity_data:dict):
    representante_comercial = entity_data.get("assigned_user_id")
    gerente_relacionamento = entity_data.get("users_accounts_1users_ida")
    conta_mestre = entity_data.get("parent_id")
    s, r = dal_crm.GetObject(CRM, module="accounts", filtro={'id': suite_id})
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
            for conta in GetAccount(CRM, id_conta_lm=id_conta_lm):
                _dados["id"] = conta.get('id')
                if _dados["id"] != suite_id:
                    _s, _d = dal_crm.PutObject(CRM, module="accounts", entity_data=_dados)
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
    return dal_crm.GetObject(CRM, module=module, filtro=filtro)


def Put(module:str, entity_data:dict) -> tuple[bool, dict]:
    CRM = SuiteCRM.SuiteCRM(logger)
    if module in ['conta']:
        module = 'accounts'
        id_cliente = entity_data.get('id_cliente')
        if id_cliente:
            del entity_data['id_cliente']
            s, d = dal_crm.GetObject(CRM, module, filtro={'id_cliente_c': id_cliente})
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

    s, d = dal_crm.PutObject(CRM, module=module, entity_data=entity_data)
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
    s, d = dal_crm.PostObject(CRM, module=module, entity_data=entity_data)
    suite_id = d.get('data',{}).get('id') if d else None
    if suite_id and module == 'accounts':
        # trata as informações que devem ser as mesmas para todas as contas com o mesmo id_conta_lm_
        _infosComuns(CRM, suite_id, entity_data)
    return s, d


def Delete(module:str, entity_data:dict) -> bool:
    CRM = SuiteCRM.SuiteCRM(logger)
    return dal_crm.DeleteObject(CRM, module=module, entity_data=entity_data)


def ajusta_dict(data:dict, key:str, alt_key:str) -> any:
    x1 = data.get(key)
    x2 = data.get(alt_key)
    if x2:
        del data[alt_key]
    r = x1 if x1 else x2
    data[key] = r
    return r


def descobreIDs_RC_GC_ER(CRM:SuiteCRM.SuiteCRM, RC_name:str=None, GC_name:str=None, ER_name:str=None) -> tuple[str, str, str]:
    RC_id, GC_id, ER_id = None, None, None

    # descobre o id do RC
    if RC_name:
        user = dal_crm.User_Get(CRM, username=RC_name)
        if user and len(user) == 1:
            RC_id = user[0].get('id')
        else:
            logger.critical(f"Não achou o RC {RC_name}")
        
    # descobre o id do GC
    if GC_name:
        user = dal_crm.User_Get(CRM, username=GC_name)
        if user and len(user) == 1:
            GC_id = user[0].get('id')
        else:
            logger.critical(f"Não achou o GC {GC_name}")
    
    # descobre o id do Especialista
    if ER_name:
        user = dal_crm.User_Get(CRM, username=ER_name)
        if user and len(user) == 1:
            ER_id = user[0].get('id')
        else:
            logger.critical(f"Não achou o Especialista {ER_name}")

    return RC_id, GC_id, ER_id


def pegaIDs_grupos_seguranca(CRM:SuiteCRM.SuiteCRM, RC_id:str=None, GC_id:str=None, ER_id:str=None) -> str:
    grupos = ""

    # descobre o grupo do RC
    if RC_id:
        user = dal_crm.User_Get(CRM, id=RC_id)
        if user and len(user) == 1:
            s, grp_RC = dal_crm.SecurityGroup_Get(CRM, name=f"Rep. Com. {user[0].get('user_name')}")
            if (not s) and len(grp_RC) == 1:
                grupos = f"{grp_RC[0]['id']},"
            else:
                logger.critical(f"Não achou o grupo Rep. Com. {user[0].get('user_name')}")
        
    # descobre o grupo do GC
    if GC_id:
        user = dal_crm.User_Get(CRM, id=GC_id)
        if user and len(user) == 1:
            s, grp_GC = dal_crm.SecurityGroup_Get(CRM, name=f"Gerente {user[0].get('user_name')}")
            if (not s) and len(grp_GC) == 1:
                grupos += f"{grp_GC[0]['id']},"
            else:
                logger.critical(f"Não achou o grupo Gerente {user[0].get('user_name')}")
    
    # descobre o grupo do ER
    if ER_id:
        user = dal_crm.User_Get(CRM, id=ER_id)
        if user and len(user) == 1:
            s, grp_ER = dal_crm.SecurityGroup_Get(CRM, name=f"Especialista {user[0].get('name')}")
            if (not s) and len(grp_ER) == 1:
                grupos += f"{grp_ER[0]['id']},"
            else:
                logger.critical(f"Não achou o grupo Especialista {user[0].get('name')}")

    # normaliza a resposta
    if grupos:
        return grupos[:-1]
    return ""


def cria_BOconta(CRM:SuiteCRM.SuiteCRM, name:str, id_conta_lm:str, assigned_user_id:str, gerente_relacionamento_id:str, security_ids:str) -> tuple[str, dict]:
    # cria BOAccount
    s, BOAccount = dal_crm.BOAccount_Create(CRM, {
                                            'name': name, 
                                            'id_conta_lm': id_conta_lm, 
                                            'assigned_user_id': assigned_user_id,
                                            'gerente_relacionamento_id': gerente_relacionamento_id,
                                            'security_ids': security_ids
                                        })
    if s:
        # não foi possível criar a BOAccount
        logger.critical(f"BOAccount: Não foi criado. Erro:{s}")
        return f"BOAccount: Não foi criado. Erro:{s}", dict()
    else:
        return None, BOAccount


def sync_bu(CRM:SuiteCRM.SuiteCRM=None, account_data:dict=dict()) -> str:
    if not CRM:
        CRM = SuiteCRM.SuiteCRM(logger) 

    ajusta_dict(account_data, 'atividade_principal_c', 'atividade_principal')
    ajusta_dict(account_data, 'email1', 'email')
    ajusta_dict(account_data, 'documento_cliente_c', 'documento_cliente')
    ajusta_dict(account_data, 'bu_id_c', 'bu_id')
    ajusta_dict(account_data, 'carteira_c', 'carteira')
    representante_comercial_name = ajusta_dict(account_data, 'assigned_user_name', 'representante_comercial')
    gerente_relacionamento_name = ajusta_dict(account_data, 'gerente_relacionamento_name', 'gerente_conta')

    id_cliente = ajusta_dict(account_data, 'id_cliente_c', 'id_cliente')
    if not id_cliente:
        return "BU [id_cliente] não informado"

    # pega a BU com esse id_cliente
    crm_BU = GetAccount(CRM, id_cliente=id_cliente)
    if crm_BU:
        if len(crm_BU) == 1:
            crm_BU = crm_BU[0]
        elif len(crm_BU) > 1:
            return f"BU: Encontrado {len(crm_BU)} registros com id_cliente={id_cliente}"
    bu_nova = not crm_BU

    # É para deletar ?    
    if account_data.get('status') == 'D':
        # existe a BU ?
        if bu_nova:
            logger.warning(f"BU: Solicitação de deleção de BU inexistente, id_cliente:{id_cliente}.")
            return f"BU: Solicitação de deleção de BU inexistente, id_cliente:{id_cliente}."
        else:
            deletou = dal_crm.Account_Delete(CRM, crm_BU['id'])
            if deletou:
                return "OK"
            else:
                return f"Problemas para deletar a BU, id={crm_BU['id']}"

    # Se BU nova, testa se informou o básico
    if bu_nova and not representante_comercial_name:
        return "Representante Comercial [representante_comercial] não informado"

    if representante_comercial_name:
        account_data['assigned_user_name'] = representante_comercial_name.upper()
        representante_comercial_name = account_data['assigned_user_name']

    if gerente_relacionamento_name:
        account_data['gerente_relacionamento_name'] = gerente_relacionamento_name.upper()
        gerente_relacionamento_name = account_data['gerente_relacionamento_name']

    if bu_nova and not representante_comercial_name:
        return "Representante Comercial [representante_comercial] não informado"

    if bu_nova and not gerente_relacionamento_name:
        return "Gerente de Conta [gerente_conta] não informado"

    # Nome Fantasia ?
    if bu_nova and not account_data.get('name'):
        return "Nome Fantasia [name] não informado"

    # Razão Social ?
    v = ajusta_dict(account_data, 'razao_social_c', 'razao_social')
    if bu_nova and not v:
        return "Razao Social [razao_social] não informado"

    # id_conta_lm ?
    id_conta_lm = ajusta_dict(account_data, 'id_conta_lm_c', 'id_conta_lm')
    if not id_conta_lm:
        if bu_nova:
            return "BOAccount [id_contalm] não informado"
        else:
            id_conta_lm = crm_BU.get('id_conta_lm_c')

    if bu_nova and not id_conta_lm:
        return "BOAccount [id_contalm] não informado"

    # pega o BOAccounts com esse id_conta_lm
    BOAccount = GetBOAccount(CRM, id_conta_lm=id_conta_lm)
    if BOAccount:
        if len(BOAccount) == 1:
            BOAccount = BOAccount[0]
            # pega os ids do RC e do GC e os grupos de segurança
            RC_id = BOAccount['assigned_user_id']
            GC_id = BOAccount.get('users_gcr_contabackoffice_1users_ida')
            sec_grupo = pegaIDs_grupos_seguranca(CRM, RC_id=RC_id, GC_id=GC_id, ER_id=None)
        elif len(BOAccount) > 1:
            logger.critical(f"BOAccount: Encontrado {len(BOAccount)} registros com id_conta_lm={id_conta_lm}")
            return f"BOAccount: Encontrado {len(BOAccount)} registros com id_conta_lm={id_conta_lm}"


    # É para criar o BOAccount ?
    if not BOAccount:
        # pega os ids do RC e do GC e os grupos de segurança
        RC_id, GC_id, _ = descobreIDs_RC_GC_ER(CRM, RC_name=representante_comercial_name, GC_name=gerente_relacionamento_name, ER_name=None)
        sec_grupo = pegaIDs_grupos_seguranca(CRM, RC_id=RC_id, GC_id=GC_id, ER_id=None)

        # cria BOAccount
        s, BOAccount = cria_BOconta(CRM,
                                    name=account_data.get('name'), 
                                    id_conta_lm=id_conta_lm, 
                                    assigned_user_id=RC_id,
                                    gerente_relacionamento_id=GC_id,
                                    security_ids=sec_grupo
                                )
        if s:
            # não foi possível criar a BOAccount
            return s

    # É para criar a BU ?:
    if not crm_BU:
        # indica o BOAccount
        account_data['gcr_contabackoffice_accountsgcr_contabackoffice_ida'] = BOAccount['id'] 
        # indica o RC
        account_data['assigned_user_id'] = RC_id
        # indica o GC
        account_data['gerente_relacionamento_id'] = GC_id
        s, crm_BU = dal_crm.Account_Create(CRM, account_data)
        # criou ?
        if s:
            logger.critical(f"BU: Não foi criada. Erro:{s}, Dados:{account_data}")
            return f"BU: Não foi criada. Erro:{s}, Dados:{account_data}", None
        
        # associa a BU ao BOAccount
        dal_crm.BOAccount_AssociaBU(CRM, crm_id=BOAccount['id'] , crm_account_ids=crm_BU['id'])

        # acerta o link no BO
        dal_lm.PutSuiteID(crm_BU.get('bu_id_c'), crm_BU.get('id'))
    else: # Atualiza a BU
        # indica qual a BU
        account_data['id'] = crm_BU['id']
        s, crm_BU = dal_crm.Account_Update(CRM, account_data)
        # atualizou ?
        if s:
            return s
        
    # testa se alterou o RC ou o GC
    old_RC_id = BOAccount.get('assigned_user_id')
    old_GC_id = BOAccount.get('users_gcr_contabackoffice_1users_ida')
    if (old_RC_id != RC_id) or (old_GC_id != GC_id):
        old_sec_grupo = pegaIDs_grupos_seguranca(CRM, RC_id=old_RC_id, GC_id=old_GC_id, ER_id=None)
        dal_crm.BOAccount_RemoveGrupoSeguranca(CRM, BOAccount['id'], grupos=old_sec_grupo)

        # atualiza RC e GC do BOAccount           
        s, _ = dal_crm.BOAccount_Update(CRM, {'id': BOAccount['id'], 
                                            'assigned_user_id': RC_id, 
                                            'gerente_relacionamento_id': GC_id,
                                            'security_ids': sec_grupo,
                                            'account_ids': crm_BU['id']} )

        # acerta o GC e RC das BUs desse BOAccount
        BUs = dal_crm.BOAccount_getAccounts(CRM, BOAccount['id'])
        for BU in BUs:
            dal_crm.Account_RemoveGrupoSeguranca(CRM, BU['id'], grupos=old_sec_grupo)
            dal_crm.Account_Update(CRM, { 
                                        'id': BU['id'],
                                        'gerente_relacionamento_id': GC_id,
                                        'assigned_user_id': RC_id,
                                        'security_ids': sec_grupo
                                        }
                                    )
    else:
        # associa a BU a BOAccount
        dal_crm.BOAccount_AssociaBU(CRM, crm_id=BOAccount['id'], crm_account_ids=crm_BU['id'])

    return "OK"

def sync_contact(CRM:SuiteCRM.SuiteCRM=None, contact_data:dict=dict()) -> str:
    def deleta_contatos(crm_contatos):
        for contato in crm_contatos if crm_contatos else []:
            dal_crm.Contact_Delete(contato['id'])

    def existe_key(contact_data:dict, key:str) -> bool:
        for k, v in contact_data.items():
            if k == key:
                return True
        return False
    
    def existe_email(email:str):
        _contatos = GetContact(CRM, email=email)
        return _contatos and len(crm_contatos) == 1

    def existe_documento(doc:str):
        _contatos = GetContact(CRM, document=doc)
        return _contatos and len(crm_contatos) == 1

    def contact_merge(contact_data:dict, crm_contato:dict):
        contact_data['id'] = None
        for k, v in crm_contato.items():
            if k == 'cpf_c' and v:
                if existe_documento(v):
                    v = None
            elif k == 'email1' and v:
                if existe_email(v):
                    v = None
            elif k == 'email_addresses' and v:
                for _email_crm in v:
                    print(_email_crm)
                    if existe_email(_email_crm):
                        ...
            if v and existe_key(contact_data, k) and not contact_data.get(k):
                contact_data[k] = v
            else:
                if k == 'tipocontato_c' and v:
                    if contact_data.get(k):
                        contact_data[k] += v
                    else:
                        contact_data[k] = v
                elif k == 'email1' and v:
                    email_addresses = list()
                    # precisa fazer merge ?
                    if contact_data.get('email1'):
                        email_addresses.append({'email_address':contact_data.get('email1')})
                        del contact_data['email1']
                    contact_data['email_addresses'] = email_addresses
                elif k == 'email_addresses' and v:
                    # faz merge os emails
                    email_addresses = list()
                    for _email_crm in v:
                        email_addresses.append({'email_address':_email_crm})
                    # precisa fazer merge ?
                    if contact_data.get('email1'):
                        email_addresses.append({'email_address':contact_data.get('email1')})
                        del contact_data['email1']
                    contact_data['email_addresses'] = email_addresses
                elif k == 'phone_fax':
                    if not (contact_data.get('phone_fax') or contact_data.get('phone_whatsapp')):
                        contact_data['phone_fax'] = v


    if not CRM:
        CRM = SuiteCRM.SuiteCRM(logger) 

    if (_street:=contact_data.get('primary_address_street')):
        contact_data['primary_address_street'] = re.sub(' +', ' ', _street)

    if (_title:=contact_data.get('title')):
        contact_data['title'] = string.capwords(_title)

    ajusta_dict(contact_data, 'contatoprincipal_c', 'contatoprincipal')
    ajusta_dict(contact_data, 'tipocontato_c', 'tipocontato')

    # trata assigned_user_name
    if (assigned_user_name:=contact_data.get('assigned_user_name')):
        del contact_data['assigned_user_name']
        #contact_data['assigned_user_name'] = assigned_user_name.upper()
        contact_data['assigned_user_id'] = 1 # força ADMIN como assigned_user_id

    # retira do dict informações básicas
    id_cliente = ajusta_dict(contact_data, 'id_cliente_c', 'id_cliente')
    if id_cliente:
        del contact_data['id_cliente_c']
        # verifica se a BU existe
        crm_account = GetAccount(CRM, id_cliente=id_cliente)
        if crm_account:
            if len(crm_account) != 1:
                logger.debug(f"BU: forma encontradas {len(crm_account) if crm_account else 0} BUs com id_cliente={id_cliente}")
                return f"BU: foram encontradas {len(crm_account) if crm_account else 0} BUs com id_cliente={id_cliente}"
            crm_account = crm_account[0]
    else:
        return "BU [id_cliente] não informado"

    if (not crm_account):
        logger.debug(f"BU: Não existe no CRM BU com id_cliente={id_cliente}")
        return f"BU: Não existe no CRM BU com id_cliente={id_cliente}"
    
    fname = contact_data.get('first_name')
    lname = contact_data.get('last_name')
    if fname:
        contact_data['first_name'] = string.capwords(fname)
    if lname:
        contact_data['last_name'] = string.capwords(lname)
    if lname and not fname:
        contact_data['first_name'] = contact_data['last_name']
        contact_data['last_name'] = None
    if not fname and not lname:
        return "BU [first_name e last_name] não informados"

    # pega os grupos de segurança RC e GC desse account
    RC_id = crm_account.get('assigned_user_id')
    GC_id = crm_account.get('users_accounts_1users_ida')
    contact_data['security_ids'] = pegaIDs_grupos_seguranca(CRM, RC_id=RC_id, GC_id=GC_id, ER_id=None)

    # coloca o link com BU
    # contact_data['contact_account_id'] = crm_account.get('id')

    # 1) Busca por documento
    # 2) Busca por email
    # 3) Busca por
    crm_contato = None
    if contact_data.get('cpf_c'):
        crm_contatos = GetContact(CRM, document=contact_data.get('cpf_c'))
        if crm_contatos and len(crm_contatos) == 1:
            crm_contato = crm_contatos[0]

    # busca por email ?
    if (not crm_contato) and contact_data.get('email1'):
        crm_contatos = GetContact(CRM, email=contact_data.get('email1'))
        if crm_contatos and len(crm_contatos) == 1:
            crm_contato = crm_contatos[0]

    # busca pelas outras informações ?
    if (not crm_contato) and (contact_data.get('first_name') or
                              contact_data.get('last_name') or
                              contact_data.get('phone_work') or
                              contact_data.get('phone_mobile') or
                              contact_data.get('phone_mobile')
                            ):
        # busca por nome e telefones
        crm_contatos = GetContact(CRM, 
                                           fname=contact_data.get('first_name'),
                                           lname=contact_data.get('last_name'),
                                           phone_work=contact_data.get('phone_work'),
                                           mobile_phone=contact_data.get('phone_mobile'),
                                           whatsapp=contact_data.get('phone_mobile')
                                        )
        if crm_contatos and len(crm_contatos) == 1:
            crm_contato = crm_contatos[0]

    if crm_contato:
        contact_merge(contact_data, crm_contato)
        s, k = dal_crm.Contact_Update(CRM, contact_data)
        if s:
            return f"Contato:{contact_data['id']} não foi atualizado. Erro:{s}, Dados:{contact_data}"
    else:
        s, k = dal_crm.Contact_Create(CRM, contact_data)
        if s:
            return f"Contato não foi criado. Erro:{s}, Dados:{contact_data}"

    # associa o contato a BU
    dal_crm.Account_AssociaContatos(CRM, crm_account['id'], k['id'])

    # provisório enquanto não abre o subpainel de BUs no Contact
    # associa a BU ao contato
    # dal_crm.Contact_AssociaAccounts(CRM, k['id'], crm_account['id'])

    # coloca o contato também na conta BO ?
    BOAccount = GetBOAccount(CRM, id_conta_lm=crm_account['id_conta_lm_c'])
    if BOAccount:
        if len(BOAccount) != 1:
            logger.debug(f"BOAcccount: foram encontratos {len(BOAccount)} registros no CRM para id_conta_lm={crm_account['id_conta_lm_c']}")
            return f"BOAcccount: foram encontratos {len(BOAccount)} registros no CRM para id_conta_lm={crm_account['id_conta_lm_c']}"
        BOAccount = BOAccount[0]
        ## descobre o RC e GC da BOAccount dessa BU
        #grupos = pega_grupos_ids(CRM, RC_id=BOAccount.get('assigned_user_id'), GC_id=BOAccount.get('users_gcr_contabackoffice_1users_ida')) 
        #if grupos:
        #    _ = dal_crm.Contact_AssociaGruposSeguranca(CRM, crm_contact_id=k['id'], crm_sec_grup_ids=grupos[:-1] )
        
        # se só existe uma BU nessa BOAccount, o contato também é do BOAccount
        BUs = dal_crm.BOAccount_getAccounts(CRM, bo_account_id=BOAccount['id'])
        if len(BUs) == 1:
            dal_crm.BOAccount_AssociaContacts(CRM, BOAccount['id'], k['id'])

    return "OK"


def sync_contract(CRM:SuiteCRM.SuiteCRM=None, contract_data:dict=dict()) -> str:
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

    if CRM is None:
        CRM = SuiteCRM.SuiteCRM(logger)

    # realiza os ajustes necessários (datas e nome)                            
    for k, v in contract_data.items():
        if k in ["date_entered","start_date","end_date","customer_signed_date","company_signed_date","renewal_reminder_date","data_cancelamento_c"]:
            contract_data[k] = conv_date(v)
        elif k in ["assigned_user_name", 'especialista_relacionamento_name']:
            contract_data[k] = v.upper()

    # ajusta os campos para o CRM
    ajusta_dict(contract_data, 'data_cancelamento_c', 'data_cancelamento')
    ajusta_dict(contract_data, 'status_contrato_c', 'status_contrato')
    ajusta_dict(contract_data, 'forma_pagamento_c', 'forma_pagamento')
    ajusta_dict(contract_data, 'total_contract_value', 'valor_contrato')
    ajusta_dict(contract_data, 'valor_pago_mes_atual_c', 'valor_pago_mes_atual')
    ajusta_dict(contract_data, 'valor_pago_mes_passado_c', 'valor_pago_mes_passado')
    ajusta_dict(contract_data, 'valor_pago_mes_retrasado_c', 'valor_pago_mes_retrasado')
    contract_data['status'] = 'Signed'

    # informou o número do contrato ?
    reference_code = ajusta_dict(contract_data, 'reference_code', 'numero_contrato')
    if reference_code:
        crm_contrato = GetContract(CRM, numero=reference_code)
        contrato_novo = (not crm_contrato) or (len(crm_contrato) == 0)
    else:
        return "Número do contrato [numero_contrato] não informado"

    if not contrato_novo:
        crm_contrato = crm_contrato[0]

    if contrato_novo and not contract_data.get('name'):
        return "Contrato sem nome [name]"

    representante_comercial_name = ajusta_dict(contract_data, 'assigned_user_name', 'representante_comercial')
    if contrato_novo and not representante_comercial_name:
        return "Representante Comercial [representante_comercial] não informado"

    especialista_name = ajusta_dict(contract_data, 'especialista_relacionamento_name', 'especialista')
    if contrato_novo and not especialista_name:
        return "Especialista [especialista] não informado"

    # informou a BU ?
    id_cliente = ajusta_dict(contract_data, 'id_cliente', 'id_cliente_c')
    if contrato_novo and not id_cliente:
        return "BU [id_cliente] não informado"
    else:
        if not contrato_novo and not id_cliente:
            ContaContratante = GetAccount(CRM, id=crm_contrato.get('contract_account_id'))
        else:
            # pega a conta Contratante ?
            ContaContratante = GetAccount(CRM, id_cliente=id_cliente)
        if not ContaContratante or len(ContaContratante) != 1:
            return f"BU Contratante: foram encontrados {len(ContaContratante) if ContaContratante else 0} registros no CRM com id_cliente={id_cliente} !"
        ContaContratante = ContaContratante[0]
        id_conta_lm = ContaContratante.get('id_conta_lm_c')

    #id_conta_lm = ajusta_dict(contract_data, 'id_conta_lm', 'id_conta_lm_c')
    #if contrato_novo and not id_conta_lm:
    #    return "BOAccount [id_contalm] não informado"
    #else:
    #    # usar o id_conta_lm da ContaContratante
    #    print("todo: usar o id_conta_lm da ContaContratante")


    # ajusta a data de encerramento do contrato
    if (data_cancelamento:=contract_data.get('data_cancelamento_c')) and not contract_data.get('end_date'):
        contract_data['end_date'] = data_cancelamento

    # pega a conta BO
    BOAccount = GetBOAccount(CRM, id_conta_lm=id_conta_lm)
    if (not BOAccount) or len(BOAccount) != 1:
        return f"BOAccount: foram encontrados {len(BOAccount) if BOAccount else 0} registros no CRM com id_conta_lm={id_conta_lm} !"
    else:
        BOAccount = BOAccount[0]

    RC_id = BOAccount.get('assigned_user_id')
    GC_id = BOAccount.get('users_gcr_contabackoffice_1users_ida')
    if especialista_name:
        _, _, ER_id = descobreIDs_RC_GC_ER(CRM, RC_name=None, GC_name=None, ER_name=especialista_name)
    else:
        ER_id = crm_contrato.get('users_aos_contracts_1users_ida')

    # coloca no contrato os grupos que podem ve-lo
    grupos_sec = pegaIDs_grupos_seguranca(CRM, RC_id=RC_id, GC_id=GC_id, ER_id=ER_id)
    contract_data['security_ids'] = grupos_sec

    # coloca o id da BOAccount nos dados do contrato
    contract_data['gcr_contabackoffice_aos_contracts_id'] = BOAccount['id']

    # coloca o id da conta nos dados do contrato
    contract_data['contract_account_id'] = ContaContratante.get('id')

    # verifica se o contrato existe
    if crm_contrato:
        # se existe, atualiza as informações
        contract_data['id'] = crm_contrato.get('id')
        s, _ = dal_crm.Contract_Update(CRM, contract_data)
        if s:
            logger.debug(f"Contrato:{contract_data.get('id')} não foi atualizado. Erro:{s}, Dados:{contract_data}")
            return f"Contrato:{contract_data.get('id')} não foi atualizado. Erro:{s}, Dados:{contract_data}"
    else:
        # se não existe, cria !
        s, _ = dal_crm.Contract_Create(CRM, contract_data)
        if s:
            return f"Contrato não foi criado. Erro:{s}, Dados:{contract_data}"

    # coloca o grupo do especialita na BU Contratante
    dal_crm.Account_AssociaGruposSeguranca(CRM, ContaContratante, grupos_sec)
    return "OK"


def processa_arquivo_contas(file_path:str, skiplines:int=0):
    qtd_erros = 0
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
                    dado = row
                    if len(dado) != len(headers):
                        logger.info(f"linha:{row_num} - Quantidade de campos:{len(dado)} desta linha difere do header:{len(headers)}")
                        formatacao += 1
                        continue

                    account_data = dict()
                    for i in range(len(headers)):
                        account_data[headers[i]] = dado[i]

                    resp = sync_bu(CRM, account_data=account_data)
                    if resp !=  "OK":
                        logger.info(f"linha:{row_num} - {resp}")
                        qtd_erros += 1
                        continue

                if row_num % 50 == 0:
                    logger.info(f"Processados {row_num-1} registros, {qtd_erros} com problemas e {formatacao} com problemas de formatação")
    logger.info(f"Fim do processamento.{CRLF}{TAB}Processados {row_num-1} registros, {qtd_erros} com problemas e {formatacao} com problemas de formatação")
    return f"Fim do processamento.{CRLF}{TAB}Processados {row_num-1} registros, {qtd_erros} com problemas e {formatacao} com problemas de formatação"


def processa_arquivo_contatos(file_path:str, skiplines:int=0) -> str:
    qtd_erros = 0
    qtd_formatacao = 0
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
                        qtd_formatacao += 1
                        continue

                    contact_data = dict()
                    for i in range(len(headers)):
                        contact_data[headers[i]] = dado[i]

                    if not (contact_data.get('first_name') or contact_data.get('last_name')):
                        contact_data['first_name'] = contact_data['email1']

                    msg = sync_contact(CRM=CRM, contact_data=contact_data)
                    if msg != "OK":
                        qtd_erros += 1
                        logger.info(f"linha:{row_num} - {msg}")
                        continue

                if row_num % 50 == 0:
                    logger.info(f"Processados {row_num-1} registros, sendo {qtd_erros} com erro e {qtd_formatacao} com problemas de formato do CSV")
    logger.info(f"Processados {row_num-1} registros, sendo {qtd_erros} com erro e {qtd_formatacao} com problemas de formato do CSV")
    return f"Processados {row_num-1} registros, sendo {qtd_erros} com erro e {qtd_formatacao} com problemas de formato do CSV"


def processa_arquivo_contratos(file_path:str, skiplines:int=0) -> str:
    qtd_erros = 0
    qtd_erros_formatacao = 0
    file_path = "/mnt/shared/crm/" + file_path
    CRM = SuiteCRM.SuiteCRM(logger) 
    row_num = 1
    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)
        row_num = 0
        for row in csv_reader:
            row_num += 1      
            if row_num == 1:
                headers = row
                headers[0] = headers[0].replace('\ufeff', '').replace('"','')
                logger.info(f"Header carregado:{headers}")
            else:
                if row_num >= skiplines:
                    dado = row
                    if len(dado) != len(headers):
                        logger.info(f"linha:{row_num} - Quantidade de campos:{len(dado)} desta linha difere do header:{len(headers)}")
                        qtd_erros_formatacao += 1
                        continue
                    
                    contract_data = dict()
                    for i in range(len(headers)):
                        contract_data[headers[i]] = dado[i]

                    resposta = sync_contract(CRM=CRM, contract_data=contract_data)
                    if resposta != 'OK':
                        qtd_erros += 1

            if (row_num % 50) == 0:
                logger.info(f"Processados {row_num-1} registros, sendo {qtd_erros} com erro e {qtd_erros_formatacao} com problemas de formatação")
    logger.info(f"Fim do processamento.{CRLF}{TAB}Processados {row_num-1} registros, sendo {qtd_erros} com erro e {qtd_erros_formatacao} com problemas de formatação")
    return f"Processados {row_num-1} registros, sendo {qtd_erros} com erro e {qtd_erros_formatacao} com problemas de formatação"


def processa_arquivo_deleta_contratos(file_path:str, skiplines:int=0) -> str:
    file_path = "/mnt/shared/crm/" + file_path
    CRM = SuiteCRM.SuiteCRM(logger)
    qtd_erros_formatacao = 0
    qtd_deletados = 0 
    row_num = 1
    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)
        row_num = 0
        for row in csv_reader:
            row_num += 1      
            if row_num == 1:
                headers = row
                headers[0] = headers[0].replace('\ufeff', '').replace('"','')
                logger.info(f"Header carregado:{headers}")
            else:
                if row_num >= skiplines:
                    dado = row
                    if len(dado) != len(headers):
                        logger.info(f"linha:{row_num} - Quantidade de campos:{len(dado)} desta linha difere do header:{len(headers)}")
                        qtd_erros_formatacao += 1
                        continue
                    
                    contract_data = dict()
                    for i in range(len(headers)):
                        contract_data[headers[i]] = dado[i]
                    qtd_deletados += 1 if  dal_crm.Contract_Delete(CRM, numero=row[0]) else 0
    return f"arquivo com {row_num-1} registros processado, {qtd_deletados} contratos deletados e {qtd_erros_formatacao} erros de formatação no CSV"


def coloca_contatos_nos_BOAccounts():
    CRM = SuiteCRM.SuiteCRM(logger)     

    # pega o BOAccount
    BOAccounts = dal_crm.BOAccounts(CRM)
    for BOAccount in BOAccounts:
        print('>', end='')
        BOAccount_id = BOAccount['id']
        BUs = dal_crm.BOAccount_getAccounts(CRM, BOAccount_id)
        if BUs and len(BUs) == 1:
            contatos = dal_crm.Account_getContacts(CRM, BUs[0]['id'])
            if not contatos or len(contatos) == 0:
                print(f"BU {BUs[0]['id']} sem contato")
            else:
                for contato in contatos:
                    dal_crm.BOAccount_AssociaContacts(CRM, BOAccount_id, contato['id'])        
        if not BUs or len(BUs) == 0:
            print(f"BO {BOAccount_id} sem BU ! ")

def associa_BUs_aos_contatos():
    CRM = SuiteCRM.SuiteCRM(logger)     

    # pega as BUs
    BUs = dal_crm.Accounts(CRM)
    for BU in BUs:
        print('>', end='')
        bu_id = BU['id']
        contatos = dal_crm.Account_getContacts(CRM, bu_id)
        for contato in contatos if contatos else []:
            dal_crm.Contact_AssociaAccounts(CRM, crm_contact_id=contato['id'], crm_account_id=bu_id)

def associa_gruposseguranca_aos_contratos():
    CRM = SuiteCRM.SuiteCRM(logger)     

    # pega as BOAccounts
    BOAccounts = dal_crm.BOAccounts(CRM)
    for BOAccount in BOAccounts:
        print('>', end='')
        RC_id = BOAccount.get('assigned_user_id')
        GC_id = BOAccount.get('users_gcr_contabackoffice_1users_ida')
        
        # pega o grupo
        grupo1 = pegaIDs_grupos_seguranca(CRM, RC_id=RC_id, GC_id=GC_id, ER_id=None)
        
        # pega os contratos dessas BOAccounts
        contratos = dal_crm.BOAccount_getContracts(CRM, BOAccount['id'])
        for contrato in contratos if contratos else []:
            print('.', end='')
            RC_id = contrato.get('assigned_user_id')
            ER_id = contrato.get('users_aos_contracts_1users_ida')
            grupo2 = pegaIDs_grupos_seguranca(CRM, RC_id=RC_id, GC_id=None, ER_id=ER_id)

            # todo
            print("todo: remover os grupos anteriores")
            # associa ao contrato
            dal_crm.Contract_AssociaGruposSeguranca(CRM, crm_contract_id=contrato['id'], crm_sec_grup_ids=f"{grupo1},{grupo2}")

            # todo
            print("todo: remover os grupos anteriores")

            # associa a BU contratante
            dal_crm.Account_AssociaGruposSeguranca(CRM, crm_account_id=contrato['contract_account_id'], crm_sec_grup_ids=grupo2)

def remove_GC_de_BOAccounts_sem_contrato_ativo():
    def tem_contrato_ativo(contratos:list) -> bool:
        for contrato in contratos:
            if contrato.get('status_contrato_c','').upper() == 'ATIVO':
                return True
        return False

    CRM = SuiteCRM.SuiteCRM(logger)     

    # pega as BOAccounts
    BOAccounts = dal_crm.BOAccounts(CRM)
    for BOAccount in BOAccounts:
        print('>', end='')
        # pega os contratos dessas BOAccounts
        contratos = dal_crm.BOAccount_getContracts(CRM, BOAccount['id'])
        if not tem_contrato_ativo(contratos):
            print('.', end='')
            if (GC_id:=BOAccount['users_gcr_contabackoffice_1users_ida']):
                grupo_sec = pegaIDs_grupos_seguranca(CRM, GC_id=GC_id)
                
                # remove o GC do BOAccount
                #s, _ = dal_crm.BOAccount_Update(CRM, {'id': BOAccount['id'], 'users_gcr_contabackoffice_1users_ida': ''})
                s, _ = dal_crm.BOAccount_Update(CRM, {'id': BOAccount['id'], 'gerente_relacionamento_id': ''})
                if s:
                    print(f"Problemas para atualizar BOAccount:{BOAccount['id']}")

                # remove o grupo sec GC do BOAccount
                if grupo_sec:
                    dal_crm.BOAccount_RemoveGrupoSeguranca(CRM, BOAccount['id'], grupo_sec)
                    for contrato in contratos:
                        # remove o grupo sec GC do contrato
                        dal_crm.Contract_RemoveGrupoSeguranca(CRM, contrato['id'], grupo_sec)

                for BU in dal_crm.BOAccount_getAccounts(CRM, BOAccount['id']):
                    # remove o GC da BU
                    #dal_crm.Account_Update(CRM, {'id': BU['id'], 'users_accounts_1users_ida': ''})
                    s, _ = dal_crm.Account_Update(CRM, {'id': BU['id'], 'gerente_relacionamento_id': ''})
                    # remove o grupo sec GC do contrato
                    if grupo_sec:
                        dal_crm.Account_RemoveGrupoSeguranca(CRM, BU['id'], grupo_sec)
