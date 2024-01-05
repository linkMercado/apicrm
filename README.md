# SUITE CRM – API -

## endpoint:
http://internalapi.linkmercado.com.br/crm

## entradas:
    • /accounts	=> para Contas
    • /leads		=> para Leads
    • /opportunities	=> para Oportunidades
    • /contacts	=> para Contatos

## métodos:
    • GET		=> retorna a lista da 'entidade'
    • POST		=> cria a 'entidade'
    • PUT		=> atualiza a 'entidade'
    • DELETE	=> deleta a 'entidade'

O método GET aceita parâmetros para restringir o resultado da pesquisa

Nas chamadas usando os métodos POST e PUT e DELETE, os parâ­metros ficam no body e em formato JSON e são iguais aos campos do SuiteCRM.

Nas chamadas usando os métodos PUT e DELETE, o parâmetro id é obrigatório.

As respostas são sempre JSON com as informações:
    • status	=> "OK" ou "ERRO" (sempre presente na resposta)
    • msg	=> "mensagem de erro" (presença somente quando o status = ERRO)
    • data	=> array com as entidades solicitadas ou com o ID da entidade criada


## Alguns exemplos:
Lista todos os contatos:
```http
GET http://internalapi.linkmercado.com.br/crm/contacts
```

Lista todos os contatos com raul no nome:
```http
GET http://internalapi.linkmercado.com.br/crm/contacts?name=raul
```

Lista o contato com o ID=…:
```http
GET http://internalapi.linkmercado.com.br/crm/contacts?id=1068f1d8-578e-b861-1d13-6566a07a9e1f
```http
Resposta:
```json
{
    "data": [
        {
            "accept_status_id": "",
            "accept_status_name": "",
            "account_id": "579f77c5-9838-2d84-83ce-653878ec4cdb",
            "account_name": {
                "id": "579f77c5-9838-2d84-83ce-653878ec4cdb",
                "name": "Nosso Lar Spa Pet Serviços de Hotelaria para Cães Ltda ME"
            },
            "alt_address_city": "",
            "alt_address_country": "",
            "alt_address_postalcode": "",
            "alt_address_state": "",
            "alt_address_street": "",
            "alt_address_street_2": "",
            "alt_address_street_3": "",
            "assigned_user_id": "9111e100-ce31-231a-54d2-653289723f93",
            "assigned_user_name": {
                "id": "9111e100-ce31-231a-54d2-653289723f93",
                "user_name": "ralves"
            },
            "assistant": "",
            "assistant_phone": "",
            "birthdate": "",
            "c_accept_status_fields": {
                "id": ""
            },
            "campaign_id": "",
            "campaign_name": {
                "id": "",
                "name": ""
            },
            "contatoprincipal_c": "true",
            "cpf_c": "03808617713",
            "created_by": "9111e100-ce31-231a-54d2-653289723f93",
            "created_by_name": {
                "id": "9111e100-ce31-231a-54d2-653289723f93",
                "user_name": "ralves"
            },
            "date_entered": "2023-11-29 02:23:58",
            "date_modified": "2023-12-29 15:11:06",
            "date_reviewed": "",
            "deleted": "",
            "department": "",
            "description": "",
            "do_not_call": "",
            "e_accept_status_fields": {
                "id": ""
            },
            "e_invite_status_fields": {
                "id": ""
            },
            "email": "",
            "email1": "secretariahotelnossolar@gmail.com",
            "email2": "",
            "email_addresses": [],
            "email_addresses_non_primary": "",
            "email_and_name1": "Andréia Rocha <secretariahotelnossolar@gmail.com>",
            "email_opt_out": "",
            "event_accept_status": "",
            "event_invite_id": "",
            "event_status_id": "",
            "event_status_name": "",
            "facebook_c": "",
            "first_name": "Andréia",
            "full_name": "salutation first_name last_name",
            "id": "1068f1d8-578e-b861-1d13-6566a07a9e1f",
            "instagram_c": "",
            "invalid_email": "",
            "jjwg_maps_address_c": "",
            "jjwg_maps_geocode_status_c": "",
            "jjwg_maps_lat_c": "0.00000000",
            "jjwg_maps_lng_c": "0.00000000",
            "joomla_account_access": "",
            "joomla_account_id": "",
            "last_name": "Rocha",
            "lawful_basis": [],
            "lawful_basis_source": "",
            "lead_source": "Existing Customer",
            "m_accept_status_fields": {
                "id": ""
            },
            "modified_by_name": {
                "id": "9111e100-ce31-231a-54d2-653289723f93",
                "user_name": "ralves"
            },
            "modified_user_id": "9111e100-ce31-231a-54d2-653289723f93",
            "module_name": "Contacts",
            "name": "Andréia Rocha",
            "object_name": "Contact",
            "opportunity_role": "",
            "opportunity_role_fields": {
                "id": ""
            },
            "opportunity_role_id": "",
            "phone_fax": "",
            "phone_home": "",
            "phone_mobile": "",
            "phone_other": "",
            "phone_work": "+55 (21) 970041714",
            "photo": "",
            "portal_account_disabled": "",
            "portal_user_type": "Single",
            "primary_address_city": "Rio de Janeiro",
            "primary_address_country": "Brasil",
            "primary_address_postalcode": "23026-210",
            "primary_address_state": "RJ",
            "primary_address_street": "Rua  Várzea da Palma, S/N - Sítio 15, 0\nLt 13 ao 16",
            "primary_address_street_2": "",
            "primary_address_street_3": "",
            "report_to_name": {
                "id": "",
                "last_name": ""
            },
            "reports_to_id": "",
            "salutation": "",
            "sync_contact": "",
            "tipocontato_c": [
                "Autorizador",
                "Financeiro"
            ],
            "title": "Sócia"
        }
    ],
    "status": "OK"
}
```

Cria contato:
```http
POST http://internalapi.linkmercado.com.br/crm/contacts
```
Body:
```json
{
"first_name":"Guiiiillllherme", 
"last_name":"Souzzzzzzzzzzzzzzza", 
"phone_work":"2122662222", 
"phone_mobile":"21989998999"
}
```
Resposta:
```json
{
    "data": {
        "id": "3a73dfe8-532b-539f-ee6b-65973538b832"
    },
    "status": "OK"
}
```

Atualiza o contato com ID=...:
```http
PUT http://internalapi.linkmercado.com.br/crm/contacts
```
Body:
```json
{
 "id": "3a73dfe8-532b-539f-ee6b-65973538b832",
"first_name":"Guiiiiiillllhermeeeeeeeeeeeeeeeeeeeeeeeeeeeee", 
"last_name":"Souzzzzzzzzzzzzzzza", 
"phone_work":"2122662222", 
"phone_mobile":"21989998999"
}
```
Resposta:
```json
{
    "data": {
        "id": "3a73dfe8-532b-539f-ee6b-65973538b832"
    },
    "status": "OK"
}
```

Deleta o contato com ID=…:
```http
DELETE http://internalapi.linkmercado.com.br/crm/contacts
```
Body:
```json
{
 "id": "3a73dfe8-532b-539f-ee6b-65973538b832",
}
```
Resposta:
```json
{
    "status": "OK"
}
```