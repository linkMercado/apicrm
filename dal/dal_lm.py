# encoding: utf-8
# -*- coding: utf-8 -*-
#


from datetime import date
from apicrm import LOGGER as logger
from apicrm import MYSQLPOOL as mysql_pool


def getPoolInfo():
    return mysql_pool.getPoolInfo()


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
                , GROUP_CONCAT( u.name SEPARATOR '|') colaboradores
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
                left OUTER join backoffice_account_managers am
                    ON am.account_id = bu.account_id
                left outer JOIN linkmercado.backoffice_users u
                    ON u.id = am.id                    
                WHERE bu.id = '{buid}'"""
        respBU = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=False)
        return  respBU[0] if respBU and len(respBU) > 0 and respBU[0].get('id') else None
    return None


def PutSuiteID(buid:str, suiteid:str) -> bool:
    if buid and suiteid:
        cmd = f"UPDATE linkmercado.core_business_units SET suite_id = '{suiteid}' WHERE id = '{buid}'"
        resp = mysql_pool.execute(cmd, cursor_args={"buffered": True, "dictionary": True}, commit=True, lastInserted=True)
    return True if resp.get('rowcount', None) else False
