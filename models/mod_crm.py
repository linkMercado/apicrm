# encoding: utf-8
# -*- coding: utf-8 -*-

default_user_id = 1

def endereco(street_type, street, house_number, additional_address):
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

class Account(object):
    def _asdict(self):
        return self.__dict__

    def __init__(self, budata:dict):
            self.id = budata.get('suite_id')
            self.bu_id_c = budata.get('id')
            self.id_conta_lm_c = budata.get('account_id')
            self.id_cliente_c = budata.get('id_cliente')
            self.modified_user_id = default_user_id
            self.created_by = default_user_id

            if budata.get('corporate_name'): self.name = budata.get('corporate_name')
            if budata.get('nome_fantasia'): self.nome_fantasia_c = budata.get('nome_fantasia')

            doc = budata.get('cnpj')
            if doc is None: doc = budata.get('cpf')
            if doc: self.documento_cliente_c = doc
            # assigned_user_name: user_name do colaborador

            _endereco = endereco(budata.get('street_type'), budata.get('street'), budata.get('house_number'), budata.get('additional_address'))
            if _endereco: 
                self.billing_address_street = _endereco
                if budata.get('city'): self.billing_address_city = budata.get('city')
                if budata.get('state'): self.billing_address_state = budata.get('state')
                if budata.get('zipcode'): self.billing_address_postalcode = budata.get('zipcode')
                self.shipping_address_street = _endereco
                if budata.get('city'): self.shipping_address_city = budata.get('city')
                if budata.get('state'): self.shipping_address_state = budata.get('state')
                if budata.get('zipcode'): self.shipping_address_postalcode = budata.get('zipcode')
            
            if budata.get('latitude'): self.geo_lat_c = budata.get('latitude')
            if budata.get('longitude'): self.geo_lng_c = budata.get('longitude')


            if budata.get('facebook'): self.facebook_c = budata.get('facebook')
            if budata.get('instagram'): self.instagram_c = budata.get('instagram')
            if budata.get('website'): self.website = budata.get('website')

            if budata.get('atividade_principal'): self.atividade_principal_c = budata.get('atividade_principal')

            phones = str(budata.get('phones','')).split('|')
            if phones:
                _phone_office = ''
                _phone_alternate = '' 
                for ph in phones:
                    phone = ph.split('-')
                    if phone[0] == '6':
                        self.phone_whatsapp = f"({phone[1]}) {phone[2]}"
                    else:
                        if _phone_office:
                            if not _phone_alternate:
                                _phone_alternate = f"({phone[1]}) {phone[2]}"
                        else:
                            _phone_office = f"({phone[1]}) {phone[2]}"
                if _phone_office: self.phone_office = _phone_office
                if _phone_alternate: self.phone_alternate = _phone_alternate

            emails = budata.get('emails','').split('|')
            if len(emails) > 0:
                self.email_address = emails[0]

            colaboradores = budata.get('colaboradores')
            if colaboradores:
                colab = ', '.join(colaboradores.split('|'))
                self.employees = colab

            """
            employees: colaboradores

                   # "date_modified":
                    # "assigned_user_id":"", 
                    # "assigned_user_name":{"user_name":"","id":""},
                    # "phone_alternate":"",
                    # "email": email,
                    # "email_opt_out":"",
                    # "invalid_email":"",
                    # "email1": email,
                    
                    # "jjwg_maps_address_c":
                    # "jjwg_maps_lat_c":
                    # "jjwg_maps_lng_c":
                    # "billing_address":
                    # "shipping_address":
        """
