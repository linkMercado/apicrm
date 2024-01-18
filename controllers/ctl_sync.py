
from apicrm import LOGGER as logger

from models import mod_crm
from dal import dal_lm
from dal import dal_crm

def sync_account(buid:str, userid:str=None):
    budata = dal_lm.GetBU(buid)
    if budata:
        suite_id = budata.get('suite_id')
        entity_data = mod_crm.Account.fromBO(budata).__dict__
        if suite_id:
            # atualizar
            s, r = dal_crm.Put("accounts", entity_data=entity_data)
            return s
        else:
            # criar
            if userid:
                user = dal_lm.GetUser(userid)
                s, u = dal_crm.Get('users', {'email': user['email']})
                if s and u and len(u.get('data',[])) == 1:
                    entity_data['assigned_user_id'] = u.get('data')[0].get('id')
                else:
                    logger.warning(f"User não encontrado no SuiteCRM u:{user}")
            s, r = dal_crm.Post("accounts", entity_data=entity_data)
            if s:
                suite_id = r.get('data',{}).get('id')
                dal_lm.PutSuiteID(buid, suite_id)
                return True
            logger.critical(f"Erro ao criar Account no SuiteCRM BU:{buid}")
            return False
    return False

def sync_bo():
    s, accounts = dal_crm.Get("accounts")
    for conta in accounts.get('data',[]):
        buid = conta.get('bu_id_c')
        if buid:
            suite_id = conta.get('id')
            dal_lm.PutSuiteID(buid, suite_id)

# sync_bo()

# jb
# sync_account(19825816) # bysdev