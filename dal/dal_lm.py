# encoding: utf-8
# -*- coding: utf-8 -*-
#

from apicrm import LOGGER as logger
from apicrm import MYSQLPOOL as mysql_pool


def getPoolInfo():
    return mysql_pool.getPoolInfo()


def GetAccountBUs(accountid:str) -> dict:
    if accountid:
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
                WHERE bu.account_id = '{accountid}'
                GROUP BY bu.id
                ORDER BY fk.priority ASC"""
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


def PutSuiteID(buid:str, suiteid:str) -> bool:
    """"Atualiza o SuiteId e troca a company para LM

    Keyword arguments:
    buid    -- código da BU
    suiteid -- código da Conta no SuiteCRM
    Return: bool indicando se conseguiu ou não fazer a atualização
    """

    if buid and suiteid:
        cmd = f"""UPDATE linkmercado.core_business_units bu
                  JOIN linkmercado.core_accounts ac
                    ON ac.id = bu.account_id
                  SET bu.suite_id = '{suiteid}', ac.company_id = 3
                  WHERE bu.id = '{buid}' and bu.account_id > 1"""
        resp = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=True, lastInserted=True)
        return True if resp and resp.get('rowcount') else False
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

