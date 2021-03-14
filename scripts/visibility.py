import re
from difflib import SequenceMatcher

from bs4 import BeautifulSoup
from requests import get
from models.models import OAI_PMH, ROAR

def open_doar(repository_name):
    URL_OPEN_DOAR = f'https://v2.sherpa.ac.uk/cgi/retrieve?item-type=repository&api-key=0FCFE154-080F-11EB-8A17-20EB1577CA68&format=Json&filter=[["name","contains word","{repository_name}"]]&limit=4'
    data = get(URL_OPEN_DOAR).json()
    return {'name': data['items'][0]['repository_metadata']['name'][0]['name'],
            'host': data['items'][0]['repository_metadata']['url']} if 0 < len(data['items']) else None

def roar(repository_name):
    result_roar = ROAR.query.filter(ROAR.repository_name.like(f'%{repository_name}%')).all()
    return {'name': result_roar[0].repository_name, 'host': result_roar[0].home_page} if 0 < len(result_roar) else None

def oai_pmh(repository_name):
    result_oai = OAI_PMH.query.filter(OAI_PMH.repository_name.like(f'%{repository_name}%')).all()
    return {'name': result_oai[0].repository_name, 'host': result_oai[0].namespace_identifier} if 0 < len(result_oai) else None

def la_referencia(repository_name):
    URL_LA = f'https://www.lareferencia.info/vufind/Search/Results?lookfor={repository_name}&type=AllFields&limit=5'
    page_la = get(URL_LA)
    page_parser_la = BeautifulSoup(page_la.content, 'html.parser')
    for i in page_parser_la.find_all('div', {'class': 'result'}):
        repository_la = i.find_all('a')[3].text
        if 0.9 < SequenceMatcher(None, repository_la, repository_name).ratio():
            return {'name': repository_la, 'host': None}
    return None

def open_aire(repository_name):
    URL_OA = f'https://explore.openaire.eu/search/find?active=datasources&fv0={repository_name}&f0=q'
    page_openaire = get(URL_OA)
    page_parser_openaire = BeautifulSoup(page_openaire.content, 'html.parser')
    for i in page_parser_openaire.find_all('h6', attrs={'class': 'uk-margin-remove'}):
        if 0.9 < SequenceMatcher(None, i.text, repository_name).ratio():
            return {'name': i.text, 'host': None}
    return None

def google_scholar(repository_url):
    repository_url =  repository_url.replace('https://', '').replace('http://', '')
    params = {
        'api_key': '1EC0E82545D44B5A9618F3DE0896BF50',
        'search_type': 'scholar',
        'q': repository_url
    }
    api_result = get('https://api.scaleserp.com/search', params)
    results_scholar = api_result.json()['scholar_results'] if 'scholar_results' in api_result.json() else []
    if 0 < len(results_scholar):
        return {'name': None, 'host': results_scholar[0]['domain']}
    return None

def standard_name(data):
    if 1 < len(data):
        first = data[next(iter(data))]['name']
        for key in data:
            if data[key]['name'] and first != data[key]['name']:
                return 1.5
    return 0

def friendly_secure_url(repository_url):
    if 'https' in repository_url:
        host_clear = repository_url.replace('https://', '')
        if len(host_clear) < 40 and re.match(r'^[a-z0-9.-/]+$', host_clear):
            return 1.5
    return 0

def boai(repository_name):
    URL_BOAI = f'https://www.budapestopenaccessinitiative.org/list_signatures?indorg=all&keyword={repository_name}'
    page_boai = get(URL_BOAI)
    page_parser_boai = BeautifulSoup(page_boai.content.decode('utf-8'), 'html.parser')
    for i in page_parser_boai.find('div', attrs={'id': 'search-signatures'}).find_all('tr'):
        if 0.85 < SequenceMatcher(None, i.find_all('td')[0].text, repository_name).ratio():
            return 1
    return 0

def count_items(data, items):
    count = 0
    for i in items:
        if data[i]:
            count += 1
    return count if count == 0 or count == 1 else 1.5

def execute(data):
    results = {}
    if 'repository_name' in data and 'repository_url' in data:
        results['OpenDoar'] = open_doar(data['repository_name'])
        results['ROAR'] = roar(data['repository_name'])
        results['OAI-PMH'] = oai_pmh(data['repository_name'])
        results['LA-Referencia'] = la_referencia(data['repository_name'])
        results['OpenAIRE'] = open_aire(data['repository_name'])
        results['Google-Scholar'] = google_scholar(data['repository_url'])
        return {
            'directory': count_items(results, ['OpenDoar', 'ROAR', 'OAI-PMH']),
            'collector': count_items(results, ['LA-Referencia', 'OpenAIRE', 'Google-Scholar']),
            'standard': standard_name(results),
            'url': friendly_secure_url(data['repository_url']),
            'boai': 1 if boai(data['repository_name']) else 0
        }
    return {'error': 'Falta información'}
