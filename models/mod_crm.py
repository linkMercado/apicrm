# encoding: utf-8
# -*- coding: utf-8 -*-

default_user_id = "1"
default_lead_id = "277d152e-1358-434b-8d0e-65a199598290",



class Account(object):
    def _asdict(self):
        return self.__dict__

    def __init__(self):
        pass

    @staticmethod
    def __endereco(street_type, street, house_number, additional_address):
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
            cls.created_by = default_user_id
        cls.modified_user_id = default_user_id

        if budata.get('id'): cls.bu_id_c = budata.get('id')
        if budata.get('account_id'): cls.id_conta_lm_c = budata.get('account_id')
        if budata.get('id_cliente'): cls.id_cliente_c = budata.get('id_cliente')

        if budata.get('corporate_name'): cls.name = budata.get('corporate_name')
        if budata.get('nome_fantasia'): cls.nome_fantasia_c = budata.get('nome_fantasia')

        doc = budata.get('cnpj')
        if doc is None: doc = budata.get('cpf')
        if doc: cls.documento_cliente_c = doc
        # assigned_user_name: user_name do colaborador

        _endereco = Account.__endereco(budata.get('street_type'), budata.get('street'), budata.get('house_number'), budata.get('additional_address'))
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
        if budata.get('website'): cls.website = f"https://{budata.get('website').replace('http://','').replace('https://','')}"

        if budata.get('atividade_principal'): cls.atividade_principal_c = budata.get('atividade_principal')

        phones = budata.get('phones')
        if phones:
            _phones = phones.decode().split('|')
            _phone_office = ''
            _phone_alternate = '' 
            for ph in _phones:
                phone = ph.split('-')
                if phone[0] == '6':
                    cls.phone_whatsapp = f"({phone[1]}) {phone[2]}"
                else:
                    if _phone_office:
                        if not _phone_alternate:
                            _phone_alternate = f"({phone[1]}) {phone[2]}"
                    else:
                        _phone_office = f"({phone[1]}) {phone[2]}"
            if _phone_office: cls.phone_office = _phone_office
            if _phone_alternate: cls.phone_alternate = _phone_alternate

        emails = budata.get('emails')
        if emails:
            _emails = emails.split('|')
            if len(_emails) > 0:
                cls.email_address = _emails[0]

        # colaboradores = budata.get('colaboradores')
        # if colaboradores:
        #    colab = ', '.join(colaboradores.split('|'))
        #    self.employees = colab
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
        cls.phone_home = dudaform['telefone']
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