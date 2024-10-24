# encoding: utf-8
# -*- coding: utf-8 -*-

import re
from datetime import datetime

from dal import dal_crm
from apicrm import SUITECRM as SuiteCRM 
API_GEN_UserID = "e53b04f5-d41d-e195-e970-65e720c0cda5"

def convLead2BU(leaddata:dict, rc_email:str) -> any:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    contato_nome = leaddata.get("name")
    contato_email = leaddata.get("email1")
    contato_telefone = SuiteCRM.format_phone(leaddata.get("phone_home"),internacional=True)
    contato_cpf = re.sub('[^0-9]', '', leaddata.get("cpf_contato_c",''))

    empresa_nome = leaddata.get("department")
    empresa_documento = re.sub('[^0-9]', '', leaddata.get("documento_c",''))
    empresa_tiporua = leaddata.get("tipo_logradouro_c",'')
    empresa_rua = leaddata.get("nome_logradouro_c",'')
    empresa_porta = leaddata.get("numero_c")
    empresa_complemento = leaddata.get("complemento_c")
    empresa_bairro = leaddata.get("nome_bairro_c",'')
    empresa_cidade = leaddata.get("nome_cidade_c",'')
    empresa_uf = leaddata.get("estado_c",'').upper()
    #empresa_cep =  re.sub('[^0-9]', '', leaddata.get("primary_address_postalcode",''))
    if (_phone:=SuiteCRM.format_phone(leaddata.get("phone_work"), internacional=True)):
        empresa_ddd = _phone[2:4]
        empresa_telefone = _phone[4:]
    else:        
        empresa_ddd = ""
        empresa_telefone = ""
    empresa_atividade = dal_crm.Atividade_GetCorpId(id=leaddata.get("gcr_titulos_id_c"))
    empresa_email = "" 

    falta = ""
    if not contato_nome:
        falta += "nome do contato,"
    if not contato_email:
        falta += "email do contato,"
    if not contato_telefone:
        falta += "telefone do contato,"
    if not contato_cpf:
        falta += "documento do contato,"

    if not empresa_nome:
        falta += "nome da empresa,"        
    if not empresa_documento:
        falta += "CNPJ da empresa,"        
    if not empresa_tiporua and not empresa_rua:
        falta += "endereço da empresa,"        
    if not empresa_porta:
        falta += "número da porta da empresa,"        
    if not empresa_cidade:
        falta += "cidade da empresa,"        
    if not empresa_uf:
        falta += "estado da empresa,"        
    if not empresa_atividade:
        falta += "atividade da empresa,"        
    if falta:
        return falta[:-1]
    return {
            "bus": [
                {
                    "origem": "CRM",
                    "grupo": {
                        "codigo": "0",
                        "nome": empresa_nome,
                        "email": empresa_email if empresa_email else contato_email,
                    },
                    "empresa": {
                        "lead_id" : leaddata['id'],
                        "rc_requestor": rc_email,
                        "conta": "0",
                        "id": "0_0_0_0",
                        "status": 0,
                        "autorizador": {
                            "telefone": contato_telefone,
                            "senha": "",
                            "email": contato_email,
                            "nome": contato_nome,
                            "email_alternativo": "",
                            "cpf": contato_cpf,
                        },
                        "razao_social": empresa_nome,
                        "documento": empresa_documento,
                        "documento_publica": False,
                        "origem": "CRM",
                        "origem_data": now
                    },
                    "endereco": {
                        "uf": empresa_uf,
                        "cidade": empresa_cidade,
                        "bairro": empresa_bairro,
                        "tipo_logradouro": empresa_tiporua,
                        "logradouro": empresa_rua,
                        "numero": empresa_porta,
                        "complemento": empresa_complemento,
                        "referencia": "",
                        #"cep": empresa_cep,
                        "visibilidade": 4,
                        "origem": "CRM",
                        "origem_data": now
                    },
                    "infos": [
                        {
                            "id": "0_0_0_0",
                            "agrupamento": "",
                            "contrato": " ",
                            "nome": empresa_nome,
                            "descricao": "",
                            "descricao_longa": "",
                            "telefones": [
                                {
                                    "__ddd": empresa_ddd,
                                    "numero": empresa_telefone,
                                    "ramal": "",
                                    "principal": True,
                                    "publica": True,
                                    "sigiloso": False,
                                    "ordem": 1,
                                    "tipo": "WhatsApp" if empresa_telefone[1] =="9" else "Cel",
                                    "ddd": empresa_ddd,
                                    "departamento": "",
                                    "origem": "CRM",
                                    "origem_data": now
                                }
                            ],
                            "atividade": empresa_atividade,
                            "url": "",
                            "url_reserva": "",
                            "produtos": [],
                            "formas_de_pagamento": [],
                            "logo": "",
                            "emails": [empresa_email],
                            "principal": True,
                            "divulgacao": {
                                "custo": 0.0,
                                "data_inicio_divulgacao": now,
                                "data_termino_divulgacao": "2050-01-01 00:00:00",
                                "materia": "",
                                "acao": "INCLUIR",
                                "cobertura": f"@{empresa_cidade.upper()}#{empresa_uf}",
                                "prioridade": "10"
                            }
                        }
                    ],
                    "keyf": f"{empresa_uf.upper()}{empresa_cidade.upper()}{empresa_tiporua.upper()}{empresa_rua.upper()}{empresa_porta}".replace(' ','')
                }
            ],
            "problemasDeEnderecamento": False,
            "idcontalm": "0",
            "tipocontalm": "P",
            "autorizador": {
                "telefone": "",
                "senha": "",
                "email": contato_email,
                "nome": contato_nome,
                "email_alternativo": "",
                "cpf": contato_cpf,
            },
            "conta": "",
            "origem": "CRM"
        }

class Account(object):
    def _asdict(self):
        return self.__dict__

    def __init__(self):
        pass

    @staticmethod
    def _endereco(street_type, street, house_number, additional_address):
        end = ''
        if street_type:
            end += street_type + ' '
        if street:
            end += street + ' '
        if house_number:
            end += f", {house_number} "
        if additional_address:
            end += f"- {additional_address}"
        return end.strip()

    @classmethod
    def fromBO(cls, budata:dict):
        cls = Account()
        _suite_id = budata.get('suite_id')
        if _suite_id: 
            cls.id = _suite_id
        else:
            cls.created_by = API_GEN_UserID
        cls.modified_user_id = API_GEN_UserID
        cls.status_c = 'Ativo' if budata.get('status') == 0 else 'Inativo'

        if budata.get('bu_id'): cls.bu_id_c = budata.get('bu_id')
        if budata.get('account_id'): cls.id_conta_lm_c = budata.get('account_id')
        if budata.get('id_cliente'): cls.id_cliente_c = budata.get('id_cliente')


        if budata.get('nome_fantasia'): cls.name = budata.get('nome_fantasia')
        if budata.get('corporate_name'): cls.razao_social_c = budata.get('corporate_name')

        doc = budata.get('cnpj')
        if doc is None: doc = budata.get('cpf')
        if doc: cls.documento_cliente_c = doc

        _endereco = Account._endereco(budata.get('street_type'), budata.get('street'), budata.get('house_number'), budata.get('additional_address'))
        if _endereco:
            cls.billing_address_street = _endereco
            if budata.get('state'): cls.billing_address_country = "Brasil"
            if budata.get('state'): cls.billing_address_state = budata.get('state').upper()
            if budata.get('city'): cls.billing_address_city = budata.get('city')
            if budata.get('zipcode'): cls.billing_address_postalcode = budata.get('zipcode')
            cls.shipping_address_street = _endereco
            if budata.get('state'): cls.shipping_address_country = "Brasil"
            if budata.get('state'): cls.shipping_address_state = budata.get('state').upper()
            if budata.get('city'): cls.shipping_address_city = budata.get('city')
            if budata.get('zipcode'): cls.shipping_address_postalcode = budata.get('zipcode')

        if budata.get('latitude'): cls.geo_lat_c = budata.get('latitude')
        if budata.get('longitude'): cls.geo_lng_c = budata.get('longitude')

        if budata.get('facebook'): cls.facebook_c = budata.get('facebook')
        if budata.get('instagram'): cls.instagram_c = budata.get('instagram')
        if budata.get('twitter'): cls.twitter_c = budata.get('twitter')
        if budata.get('linkedin'): cls.linkedin_c = budata.get('linkedin')
        if budata.get('youtube'): cls.youtube_c = budata.get('youtube')
        if budata.get('tiktok'): cls.tiktok_c = budata.get('tiktok')

        if budata.get('website'): cls.website = f"https://{budata.get('website').replace('http://','').replace('https://','')}"

        if budata.get('atividade_principal'): cls.atividade_principal_c = budata.get('atividade_principal')

        phones = budata.get('phones')
        if phones:
            _phones = phones.decode().split('|')
            _phone_office = None
            _phone_alternate = None
            _phone_whatsapp = None
            for ph in _phones:
                phone = ph.split('-')
                if phone[0] in ['6','8','1']:
                    if not _phone_whatsapp:
                        _phone_whatsapp = f"{phone[1]}{phone[2]}"
                else:
                    if _phone_office:
                        if not _phone_alternate:
                            _phone_alternate = f"{phone[1]}{phone[2]}"
                    else:
                        _phone_office = f"{phone[1]}{phone[2]}"
                if _phone_office and _phone_alternate and _phone_whatsapp:
                    # se já achou os 3 telefones, sai do loop
                    break
            if _phone_office: 
                cls.phone_office = _phone_office
            elif _phone_whatsapp:
                cls.phone_office = phone=_phone_whatsapp
            if _phone_alternate: cls.phone_alternate = _phone_alternate
            if _phone_whatsapp: cls.phone_whatsapp = _phone_whatsapp

        emails = budata.get('emails')
        if emails:
            _emails = emails.split('|')
            if len(_emails) > 0:
                cls.email_address = _emails[0]
        return cls
    

class Lead(object):
    def _asdict(self):
        return self.__dict__

    def __init__(self):
        pass

    @classmethod
    def fromDudaForm(cls, dudaform:dict):
        cls = Lead()
        cls.job_criou_lead_c = 'api_crm_dudaform'
        cls.email_address = dudaform['email']
        cls.phone_home = dudaform.get('telefone')
        cls.descricao_lead_c = dudaform['mensagem']
        _nome = dudaform['nome'].split(' ')
        if len(_nome) > 1:
            cls.first_name = _nome.split(' ')[0]
            cls.first_name = ' '.join(_nome[1:])
        else:
            cls.first_name = _nome[0]
        cls.description = dudaform['assunto']
        cls.date_entered = dudaform['event_date']
        return cls

    @classmethod
    def fromRdStationWebhook(cls, rddata:dict) -> 'Lead':
        cls = Lead()
        cls.origem = 'WPP' if rddata.get('conversion_identifier') == "lm-faleconosco" else 'FORM'
        if rddata.get('domain'): cls.dominio = rddata.get('domain')
        if rddata.get('company'): cls.department = rddata.get('company')
        if rddata.get('email'): cls.email_address = rddata.get('email')
        if rddata.get('personal_phone'): cls.phone_home = rddata.get('personal_phone')
        if rddata.get('mobile_phone'): cls.phone_fax = rddata.get('mobile_phone') 
        _nome = rddata.get('name','').strip().split(' ')
        if len(_nome) > 1:
            cls.first_name = _nome[0]
            cls.last_name = (' '.join(_nome[1:])).strip()
        else:
            cls.first_name = _nome[0].strip()
        cls.date_entered = rddata.get('wpp_date')
        cls.job_criou_lead_c = 'api_crm_rdstationwebhook'
        cls.lead_source = 'Campaign'
        cls.chegou_atraves_c = 'google_ads'
        cls.canal_de_entrada_c = 'whatsapp'
        return cls



class Contact(object):
    def _asdict(self):
        return self.__dict__

    def __init__(self):
        pass

    @classmethod
    def fromBO(cls, bodata:dict):    
        cls = Contact()
        names = bodata['name'].split(' ') if bodata.get('name') else ['sem primeiro nome', 'sem último nome']
        cls.first_name = names[0]
        if len(names) > 1:
            cls.last_name = ' '.join(names[1:])
        if bodata.get('email'):
            cls.email_address = bodata['email']
        if bodata.get('document'):
            cls.cpf_c = bodata['document']
        if (_phone:=bodata.get('phone')):
            cls.phone_work = _phone
        if (_phone:=bodata.get('mobile_phone')):
            cls.phone_mobile = _phone
        if (_phone:=bodata.get('phone_whatsapp')):
            cls.phone_fax = _phone
        if bodata.get('principal',0) == 1:
            cls.contatoprincipal_c = 1
            cls.tipocontato_c = ['^Autorizador^']
        else:
            cls.tipocontato_c = ['^Usuariobackoffice^']
        return cls

    @classmethod
    def fromLead(cls, lead_data:dict):    
        cls = Contact()
        cls.first_name = lead_data['first_name'] if lead_data.get('first_name') else 'sem primeiro nome'
        cls.last_name = lead_data.get('last_name')
        cls.email1 = lead_data.get('email1')
        cls.cpf_c = re.sub('[^0-9]', '', lead_data.get('cpf_c',''))
        cls.phone_work = lead_data.get('phone_work')
        cls.phone_fax = lead_data.get('phone_fax')
        cls.phone_home = lead_data.get('phone_home')
        cls.phone_mobile = lead_data.get('phone_mobile')
        cls.phone_other = lead_data.get('phone_other')
        cls.salutation = lead_data.get('salutation')
        cls.contatoprincipal_c = 1
        cls.tipocontato_c = ['Autorizador']
        return cls



class BOConta(object):
    def _asdict(self):
        return self.__dict__

    def __init__(self, name, representante_comercial_id, id_conta_lm, gerente_conta_id):
        self.name = name
        self.assigned_user_id = representante_comercial_id
        self.id_conta_lm = id_conta_lm
        self.user_id_c = gerente_conta_id

    @classmethod
    def fromBO(cls, bodata:dict):    
        return BOConta(bodata['nome_conta_lm'], bodata['RC_id'], bodata['id_conta_lm'], bodata['GC_id'])
