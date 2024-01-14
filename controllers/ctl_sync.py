
from apicrm import LOGGER as logger

from models import mod_crm
from dal import dal_lm
from dal import dal_crm

def sync_account(buid:str):
    budata = dal_lm.GetBU(buid)
    if budata:
        suite_id = budata.get('suite_id')
        if suite_id:
            # atualizar
            s, r = dal_crm.Put("accounts", entity_data=mod_crm.Account(budata).__dict__)
            return s
        else:
            # criar
            s, r = dal_crm.Post("accounts", entity_data=mod_crm.Account(budata).__dict__)
            if s:
                suite_id =r.get('data',{}).get('id')
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