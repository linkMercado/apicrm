# encoding: utf-8
# -*- coding: utf-8 -*-
#

from apicrm import LOGGER as logger
from apicrm import MYSQLPOOL as mysql_pool


def getPoolInfo():
    return mysql_pool.getPoolInfo()


def GetBUs(accountid:str) -> dict:
    if accountid:
        cmd = f"""SELECT
                  SUBSTRING_INDEX(fk.fk,'_',1) id_cliente
                , sx.contract_number
                , bu.status
                , SUBSTRING_INDEX(SUBSTRING_INDEX(fk.fk,'_',2),'_',-1) contrato_expandido
                , bu.id bu_id
                , bu.corporate_name, bu.cpf, bu.cnpj, bu.account_id, bu.suite_id
                , s.name state 
                , c.name city
                , ifnull(d.name,'') bairro
                , ad.street_type
                , ad.street
                , ad.house_number
                , ad.additional_address
                , ad.zipcode
                , ad.latitude
                , ad.longitude
                , pa.name atividade_principal
                , bi.name nome_fantasia
                , bi.facebook
                , bi.instagram
                , bi.twitter
                , bi.linkedin
                , bi.youtube
                , bi.tiktok
                , case when bi.url LIKE '%telelistas.com.br%' then '' else replace(replace(bi.url,'http://',''),'https://','') END website
                , GROUP_CONCAT( DISTINCT CONCAT(ph.phone_type_id,'-',ph.area_code,'-',ph.number)  ORDER BY ph.sort_order SEPARATOR '|' ) phones
                , GROUP_CONCAT( DISTINCT em.address order BY  em.id  SEPARATOR '|') emails
                FROM linkmercado.core_business_units bu
                JOIN linkmercado.core_addresses ad
                    ON ad.business_unit_id = bu.id
                JOIN linkmercado.core_states s
                    ON s.id = ad.state_id
                JOIN linkmercado.core_cities c
                    ON c.id = ad.city_id	
                LEFT OUTER JOIN linkmercado.core_districts d
                    ON d.id = ad.district_id
                LEFT OUTER JOIN linkmercado.core_business_infos bi
                    ON bi.business_unit_id = bu.id
                        AND bi.`default` = 1
                LEFT OUTER JOIN linkmercado.core_professional_activities pa
                    ON pa.id = bi.professional_activity_id
                LEFT OUTER JOIN linkmercado.data_import_business_info_fks fk
                    ON fk.business_info_id = bi.id
                LEFT OUTER JOIN linkmercado.core_phones ph
                    ON ph.business_info_id = bi.id
                    AND ph.phone_type_id <> 5
                    AND ph.publishable = 1
                LEFT OUTER JOIN linkmercado.core_emails em
                    ON em.business_info_id = bi.id
                LEFT OUTER JOIN products_contracts.subscriptions sx
                    ON sx.business_unit_id = bu.id AND sx.status = 0
                WHERE bu.account_id = '{accountid}'
                GROUP BY bu.id
                ORDER BY bu.status ASC, fk.priority DESC"""
        respBU = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=False)
    else:
        respBU = None
    return respBU


def GetAccountsIDs(buids:list) -> dict:
    if buids:
        sbuids = "','".join(buids)
        cmd = f"""SELECT bus.account_id, GROUP_CONCAT(bus.id SEPARATOR ',') buids
                FROM linkmercado.core_business_units bu
                JOIN linkmercado.core_business_units bus
                	ON bus.account_id = bu.account_id
                WHERE bu.id IN ({sbuids}) and bu.account_id > 1
                GROUP BY bus.account_id"""
        ids = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=False)
    else:
        ids = None
    return ids


def GetBU(buid:str) -> dict:
    if buid:
        cmd = f"""SELECT bu.*
                , s.name state 
                , c.name city
                , ifnull(d.name,'') bairro
                , ad.street_type
                , ad.street
                , ad.house_number
                , ad.additional_address
                , ad.zipcode
                , ad.latitude
                , ad.longitude
                , pa.name atividade_principal
                , bi.name nome_fantasia
                , bi.facebook
                , bi.instagram
                , bi.twitter
                , bi.linkedin
                , bi.youtube
                , bi.tiktok
                , case when bi.url LIKE '%telelistas.com.br%' then '' else replace(replace(bi.url,'http://',''),'https://','') END website
                , SUBSTRING_INDEX(fk.fk,'_',1) id_cliente
                , GROUP_CONCAT( CONCAT(ph.phone_type_id,'-',ph.area_code,'-',ph.number)  ORDER BY ph.sort_order SEPARATOR '|' ) phones
                , GROUP_CONCAT( em.address order BY  em.id  SEPARATOR '|') emails
                , GROUP_CONCAT( u.email SEPARATOR '|') colaboradores
                FROM linkmercado.core_business_units bu
                JOIN linkmercado.core_addresses ad
                    ON ad.business_unit_id = bu.id
                JOIN linkmercado.core_states s
                    ON s.id = ad.state_id
                JOIN linkmercado.core_cities c
                    ON c.id = ad.city_id	
                LEFT OUTER JOIN linkmercado.core_districts d
                    ON d.id = ad.district_id
                LEFT OUTER JOIN linkmercado.core_business_infos bi
                    ON bi.business_unit_id = bu.id
                        AND bi.`default` = 1
                LEFT OUTER JOIN linkmercado.core_professional_activities pa
                    ON pa.id = bi.professional_activity_id
                LEFT OUTER JOIN linkmercado.data_import_business_info_fks fk
                    ON fk.business_info_id = bi.id
                LEFT OUTER JOIN linkmercado.core_phones ph
                    ON ph.business_info_id = bi.id
                    AND ph.phone_type_id <> 5
                    AND ph.publishable = 1
                LEFT OUTER JOIN linkmercado.core_emails em
                    ON em.business_info_id = bi.id
                left OUTER join linkmercado.backoffice_account_managers am
                    ON am.account_id = bu.account_id
                left outer JOIN linkmercado.backoffice_users u
                    ON u.id = am.user_id
                WHERE bu.id = '{buid}' and bu.account_id > 1"""
        respBU = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=False)
        return respBU[0] if respBU and len(respBU) > 0 and respBU[0].get('id') else None
    return None


def GetUser(userid:str):
    if userid:
        cmd = f"SELECT * from linkmercado.backoffice_users where id = '{userid}'"
        respUser = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=False)
        return respUser[0] if respUser and len(respUser) > 0 and respUser[0].get('id') else None
    return None

def GetAutorizadores(accountid:str):
    if accountid:
        cmd = f"""
                SELECT u.name, u.email, u.document, u.phone, u.mobile_phone, p.role principal	
                FROM linkmercado.core_permissions p
                JOIN linkmercado.core_users u
                    ON u.id = p.user_id
                WHERE p.account_id = {accountid} AND u.status = 0 AND u.email not like '%.local'
                ORDER BY p.role DESC
        """
        autorizadores = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=False)
        return autorizadores
    return None


def GetSuiteID(buid:str) -> str:
    if buid:
        cmd = f"""SELECT id, suite_id
                FROM linkmercado.core_business_units
                WHERE id = {buid}"""
        resp = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=False)
        if resp and len(resp) > 0 and resp[0]['id']:
            return resp[0]['suite_id']
        else:
            return -1
        # return resp[0]['suite_id'] if resp and len(resp) > 0 and resp[0]['id'] else '-1'
    return None


def PutSuiteID(buid:str, suiteid:str=None, leadid:str=None, rcemail:str=None) -> bool:
    """"Atualiza o SuiteId e troca a company para LM

    Keyword arguments:
    buid    -- código da BU
    suiteid -- código da Conta no CRM
    leadid  -- código do Lead no CRM
    rcemail -- email do Representante Comercial
    Return: bool indicando se conseguiu ou não fazer a atualização
    """

    if buid and (suiteid is not None or leadid or rcemail):
        set1 = f"bu.suite_id = '{suiteid}', ac.company_id = CASE WHEN '{suiteid}' = '' THEN ac.company_id ELSE 3 END" if suiteid is not None else ""
        set2 = f"bu.lead_id = '{leadid}'" if leadid else ""
        set3 = f"bu.rc_requestor = '{rcemail}'" if rcemail else ""
        set2 = f",{set2}" if set2 and set1 else set2
        set3 = f",{set3}" if set3 and (set1 or set2) else set3
        cmd = f"""UPDATE linkmercado.core_business_units bu
                  JOIN linkmercado.core_accounts ac
                    ON ac.id = bu.account_id
                  SET {set1}{set2}{set3} 
                  WHERE bu.id = '{buid}' and bu.account_id > 1"""        
        resp = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=True, lastInserted=True)
        if resp and resp.get('rowcount'):
            # avisa para o corporativo buscar essa BU caso tenha informado o LeadId
            if leadid:
                cmd = f"INSERT INTO linkmercado.data_import_corporate_queues (business_unit_id, STATUS, priority, created_at, updated_at) VALUES ({buid}, 0, 30, NOW(), NOW()"
                resp = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=True, lastInserted=True)
                if not(resp and resp.get('rowcount')):
                    logger.critical(f"Não foi possível atualizar fila sync BO->Corporativo para a BU:{buid}")
            return True
    return False


def GetContatos():
    cmd = f"""
            SELECT DISTINCT bu.suite_id, cu.name, cu.email, cu.phone, cu.mobile_phone, cu.document
            FROM linkmercado.core_business_units bu
            JOIN linkmercado.core_accounts ac
                ON ac.id = bu.account_id
            JOIN linkmercado.core_permissions p
                ON p.account_id = ac.id
            JOIN linkmercado.core_users cu
                ON cu.id = p.user_id
            WHERE bu.suite_id IS NOT NULL
                AND cu.sessions_counted > 0 AND cu.`status` = 0
                AND cu.email NOT IN ('marcela.o.peralta@gmail.com', 'fegahardo@gmail.com', 'felipe.simoes.g@hotmail.com')
                AND cu.email NOT like '%@telelistas.net'
                AND cu.email NOT like '%@linkmercado.com.br'
            ORDER BY cu.name
        """
    respContato = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=False)
    return respContato

def GetBOContas(id_conta_lm:int=None):
    if id_conta_lm:
        where = f" AND l_a.id >= {id_conta_lm} "
    else:
        where = ""
    cmd = f"""
            SELECT l_a.id id_conta_lm
            , l_a.name nome_conta_lm
            , GROUP_CONCAT(bu.suite_id SEPARATOR ',') crm_accounts
            , GROUP_CONCAT(distinct a2.users_accounts_1users_ida SEPARATOR ',') GC_id
            , GROUP_CONCAT(distinct a.assigned_user_id  SEPARATOR ',') RC_id
            FROM suitecrm.accounts a
            JOIN suitecrm.accounts_cstm a1
                ON a1.id_c = a.id
            left outer JOIN suitecrm.users_accounts_1_c a2
                ON a2.users_accounts_1accounts_idb = a.id	
            JOIN linkmercado.core_accounts l_a
                ON l_a.id = a1.id_conta_lm_c
            JOIN linkmercado.core_business_units bu
                ON bu.account_id = l_a.id	
            WHERE a.deleted = 0 
                AND a1.id_conta_lm_c > 0
                AND bu.`status` = 0
                AND a2.deleted = 0
                {where}
            GROUP BY l_a.id, l_a.name	
            ORDER BY 1
        """
    respBOContas = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=False)
    return respBOContas

def GetCRMIdContaLM_Contracts() -> dict:
    cmd = f"""
            SELECT ax.id_conta_lm_c, group_concat(cc.id SEPARATOR ',') contract_id_list
            FROM suitecrm.aos_contracts cc
            JOIN suitecrm.aos_contracts_cstm	cx
                ON cx.id_c = cc.id
            JOIN suitecrm.accounts aa
                ON aa.id = cc.contract_account_id
            JOIN suitecrm.accounts_cstm ax
                ON ax.id_c = aa.id	
                WHERE cc.deleted = 0  AND ax.id_conta_lm_c IS NOT null
                AND aa.deleted = 0
            GROUP BY ax.id_conta_lm_c	
            ORDER BY 1
        """
    resp = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=False)
    return resp


def GetCRMIdContaLM_Contacts() -> dict:
    cmd = f"""
            SELECT gc.id_conta_lm, GROUP_CONCAT(distinct ac.contact_id SEPARATOR ',') contact_id_list
            FROM suitecrm.gcr_contabackoffice gc
            JOIN suitecrm.accounts_cstm ax
                ON ax.id_conta_lm_c = gc.id_conta_lm
            JOIN suitecrm.accounts aa
                ON aa.id = ax.id_c
            JOIN suitecrm.accounts_contacts ac
                ON ac.account_id = aa.id
            WHERE aa.deleted = 0 AND gc.deleted = 0 AND ac.deleted = 0 
            and gc.id_conta_lm >= 2091921
            GROUP BY gc.id_conta_lm
            ORDER BY 1
        """
    resp = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=False)
    return resp


def Atualiza_BUsBeneficiadas() -> None:
    cmd = f"suitecrm.sp_AtualizaBUsBeneficiadas"
    mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, callproc=True, commit=True)
