from difflib import SequenceMatcher

from bs4 import BeautifulSoup
from requests import get

from scripts.tools import count_form_boolean_fields

# Temporalmente inactivo mientras la página de BOAI corrige el buscador
def boai(repository_name):
    URL_BOAI = f'https://www.budapestopenaccessinitiative.org/list_signatures?indorg=all&keyword={repository_name}'
    # URL_BOAI = f'https://www.budapestopenaccessinitiative.org/sign/signatures/'
    page_boai = get(URL_BOAI, verify=False)
    page_parser_boai = BeautifulSoup(page_boai.content.decode('utf-8'), 'html.parser')
    for i in page_parser_boai.find('div', attrs={'id': 'search-signatures'}).find_all('tr'):
        if 0.85 < SequenceMatcher(None, i.find_all('td')[0].text, repository_name).ratio():
            return 1
    return None

def get_boai_score(repository_name_list):
    for i in repository_name_list:
        if boai(i) == 1:
            return 1
    return 0

def execute_policy(form, repository_name_list):
    policy_resume =  count_form_boolean_fields(form)
    # policy_resume['boai'] = get_boai_score(repository_name_list)
    policy_resume['total'] = sum(
        policy_resume[i]['value'] if dict == type(policy_resume[i]) else policy_resume[i] for i in policy_resume)
    return policy_resume
