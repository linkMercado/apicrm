from apicrm import LOGGER as logger

import requests

def busca_candidatos(doc:str, phone:str) -> tuple[bool, list]:
    # busca candidatos no BO 
    busca_bu_url = f"http://internalapi.linkmercado.com.br/microservices/lm?document={doc}&phone={phone}"
    try: 
        response = requests.get(busca_bu_url)  # ,allow_redirects=False
        if response.status_code == 200:
            return True, response.json()
    except Exception as e:
        logger.exception(f"problemas ao chamar {busca_bu_url}, error:{e}")
        return False, []
