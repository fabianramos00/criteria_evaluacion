import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from difflib import SequenceMatcher
from xml.etree.ElementTree import fromstring

from bs4 import BeautifulSoup
from requests import get
from requests.exceptions import ConnectionError
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
    return {'name': result_oai[0].repository_name, 'host': result_oai[0].namespace_identifier} if 0 < len(
        result_oai) else None


def re3data(repository_name):
    URL_R3DATA = f'https://www.re3data.org/api/beta/repositories?query={repository_name}'
    response_re3data = get(URL_R3DATA)
    tree = fromstring(response_re3data.content)
    for i in tree:
        if 0.9 < SequenceMatcher(None, i.find('name').text, repository_name).ratio():
            print(i.find('name').text)
            return {'name': i.find('name').text, 'host': None}
    return None


def la_referencia_links(repository_name):
    URL_LA_REP = f'https://www.lareferencia.info/vufind/Search/Results?limit=5&filter%5B%5D=reponame_str%3A"{repository_name}"&type=AllFields&sort=year'
    page_la = get(URL_LA_REP)
    page_parser_la = BeautifulSoup(page_la.content, 'html.parser')
    link_list, la_links = [], []
    for i in page_parser_la.find_all('div', {'class': 'result'}):
        la_links.append(i.find_all('a')[0]['href'])
    for i in la_links:
        page_la = get('https://www.lareferencia.info' + i)
        page_parser_la_r = BeautifulSoup(page_la.content, 'html.parser')
        link_list.append(page_parser_la_r.find_all('tr')[-4].find('a')['href'])
    return link_list


def la_referencia(repository_name):
    URL_LA = f'https://www.lareferencia.info/vufind/Search/Results?lookfor={repository_name}&type=AllFields&limit=5'
    page_la = get(URL_LA)
    page_parser_la = BeautifulSoup(page_la.content, 'html.parser')
    for i in page_parser_la.find_all('div', {'class': 'result'}):
        repository_la = i.find_all('a')[3].text
        if 0.9 < SequenceMatcher(None, repository_la, repository_name).ratio():
            return {'name': repository_la, 'host': None, 'links': la_referencia_links(repository_la)}
    return None


def open_aire_links(repository_name):
    links_oa, links_rep = [], []
    URL_OA_ART = f'https://explore.openaire.eu/search/find?f0=q&fv0={repository_name}&page=1&size=10&sortBy=resultdateofacceptance,descending&resultbestaccessright="Open%2520Access"&qf=true&active=result'
    page_openaire_art = get(URL_OA_ART)
    page_parser_openaire_art = BeautifulSoup(page_openaire_art.content, 'html.parser')
    for i in page_parser_openaire_art.find_all('div', attrs={'class': 'uk-card uk-card-default uk-card-hover'}):
        data = i.find_all('div', attrs={'class': 'uk-margin-small-bottom ng-star-inserted'})
        if 0 < len(data):
            data = data[-1].text.replace('Publisher:  ', '')
            if 0.8 < SequenceMatcher(None, data, repository_name).ratio():
                links_oa.append(i.find_all('a')[0]['href'])
    for i in links_oa:
        page_oa_art = get('https://explore.openaire.eu' + i)
        page_parser_oa_art = BeautifulSoup(page_oa_art.content, 'html.parser')
        links_rep.append(
            page_parser_oa_art.find_all('div', attrs={'class': 'uk-flex uk-flex-top ng-star-inserted'})[-1].find_all(
                'a')[0]['href'])
    return links_rep


def open_aire(repository_name):
    URL_OA = f'https://explore.openaire.eu/search/find?active=datasources&fv0={repository_name}&f0=q'
    page_openaire = get(URL_OA)
    page_parser_openaire = BeautifulSoup(page_openaire.content, 'html.parser')
    for i in page_parser_openaire.find_all('div', attrs={'class': 'uk-card uk-card-default uk-card-hover'}):
        text = i.find('h6', attrs={'class': 'uk-margin-remove'}).text
        if 0.9 < SequenceMatcher(None, text, repository_name).ratio():
            link_list = i.find_all('a')
            return {'name': text, 'host': i.find_all('a')[1]['href'] if 1 < len(link_list) else None,
                    'links': open_aire_links(text)}
    return None


def google_scholar(repository_url):
    repository_url = repository_url.replace('https://', '').replace('http://', '')
    params = {
        'api_key': '1EC0E82545D44B5A9618F3DE0896BF50',
        'search_type': 'scholar',
        'q': repository_url,
        'scholar_year_min': datetime.now().year - 5,
        'scholar_include_citations': 'false'
    }
    api_result = get('https://api.scaleserp.com/search', params)
    results_scholar = api_result.json()['scholar_results'] if 'scholar_results' in api_result.json() else []
    if 0 < len(results_scholar):
        return {'name': None, 'host': results_scholar[0]['domain'],
                'links': [i['link'] for i in results_scholar if repository_url in i['domain']]}
    return None


def base(repository_name):
    URL_BASE = f'https://www.base-search.net/Search/Results?lookfor={repository_name}'
    page_base = get(URL_BASE)
    page_parser_base = BeautifulSoup(page_base.content, 'html.parser')
    base_repository = None
    art_list = []
    for i in page_parser_base.find_all('div', {'class': 'record-panel panel panel-default'}):
        repository_tmp = \
            i.find('div', {'class': 'panel-body'}).find_all('div', {'class': 'row row-eq-height'})[-4:-3][0].find_all(
                'div')[1].find(text=True, recursive=False)
        repository_tmp = repository_tmp.rstrip().lstrip()
        ratio = SequenceMatcher(None, repository_tmp.lower(), repository_name.lower()).ratio()
        art_list.append((repository_tmp, i.find('a', {'class': 'link1'})['href']))
        if 0.9 < ratio:
            if base_repository is None or base_repository['ratio'] < ratio:
                base_repository = {'name': repository_tmp, 'host': None, 'ratio': ratio}
    if base_repository is not None:
        base_repository['links'] = [i[1] for i in art_list if base_repository['name'] == i[0]]
    return base_repository


def core(repository_name):
    core_repository_name = repository_name.replace(' ', '%20')
    core_result = get(
        f'https://core.ac.uk:443/api-v2/search/{core_repository_name}?page=1&pageSize=20&apiKey=b4Z8klKuPtC1r3aeHNI2ShwdFBM6059O').json()
    core_repository = None
    if core_result['data'] is not None:
        for i in core_result['data']:
            text = i['_source']['repositories'][0]['name']
            if text is not None:
                ratio = SequenceMatcher(None, text.lower(), repository_name.lower()).ratio()
                if 0.9 < ratio:
                    if core_repository is None or core_repository['ratio'] < ratio:
                        core_repository = {'name': text, 'host': None, 'ratio': ratio}
    return core_repository


def standard_name(data):
    name_list = [{'found_in': key, 'name': data[key]['name']} for key in data if
                 data[key] and data[key]['name'] is not None]
    first = name_list[0] if len(name_list) > 0 else None
    resume = {'value': 1.5 if first is None else 0, 'details': name_list}
    for name in name_list[1:]:
        if first != name:
            resume['value'] = 0
            break
    return resume


def friendly_secure_url(repository_url):
    text, value = 'URL segura y amigable', 0
    if 'https' in repository_url:
        host_clear = repository_url.replace('https://', '')
        if len(host_clear) < 40 and re.match(r'^[a-z0-9.-/]+$', host_clear):
            value = 1.5
        else:
            text = 'URL no amigable'
    else:
        text = 'URL insegura'
    return {
        'value': value,
        'text': text
    }


def count_items(data, item_name):
    count, value, text = 0, 0, f'No tiene presencia en {item_name}'
    for i in data:
        if data[i] is not None:
            count += 1
    if count == len(data):
        value, text = 1.5, f'Presencia en {count} {item_name}'
    elif 0 < count:
        value, text = 1, f'Presencia en 1 o más {item_name}'
    return {
        'value': value,
        'text': text
    }


def count_national_collectors(collector_data):
    value, text, collector_list = 0, 'No tiene presencia en recolectores nacionales', []
    if collector_data is not None:
        collector_list = [collector_data[i] for i in collector_data if collector_data[i] is not None]
        if 5 == len(collector_list):
            value, text = 1.5, 'Presencia en 5 recolectores nacionales'
        elif 0 < len(collector_list):
            value, text = 1, 'Presencia en 1 o más recolectores nacionales'
    return {
        'value': value,
        'text': text,
        'details': collector_list
    }


def search_in(function, repository_names):
    for i in repository_names:
        result = function(i)
        if result is not None:
            return result
    return None


def is_open_access(found_in, url):
    try:
        page = get(url)
    except ConnectionError as e:
        return None
    page_parse = BeautifulSoup(page.content, 'html.parser')
    meta_list = page_parse.find_all('meta', {'name': 'DC.rights'})
    for i in meta_list:
        if 'openAccess' in i['content']:
            is_open, author_rights = True, True
            break
    else:
        is_open, author_rights = False, True if 0 < len(meta_list) else False
    return {
        'url': url,
        'found_in': found_in,
        'open_access': is_open,
        'author_rights': author_rights
    }


def open_access(visibility_dict):
    link_list, dict_list, value = [], [], 1
    with ThreadPoolExecutor(max_workers=3) as executor:
        for i in visibility_dict:
            if visibility_dict[i] is not None and 'links' in visibility_dict[i]:
                for url in visibility_dict[i]['links']:
                    task_result = executor.submit(is_open_access, i, url).result()
                    if task_result:
                        if not task_result['open_access']:
                            link_list.append((i, task_result['url']))
                            value = 0
                        dict_list.append(task_result)
    return {'value': value, 'details': link_list}, dict_list


def execute_pool_thread(task_dict, repository_name_list):
    result_dict = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        result_dict = {i: executor.submit(search_in, task_dict[i], repository_name_list).result() for i in task_dict}
    return result_dict


def execute_visibility(data, form):
    initiatives_existence, national_collector = form['initiatives_existence'], form['national_collector']
    del form['national_collector'], form['initiatives_existence']
    functions_dict = {
        'OpenDoar': open_doar,
        're3data': re3data,
        'LA-Referencia': la_referencia,
        'OpenAIRE': open_aire,
        'BASE': base,
        'CORE': core
    }
    result_pool = execute_pool_thread(functions_dict, data['repository_names'])
    resume_visibility = {
        'directory': {
            'details': {
                'OpenDoar': result_pool['OpenDoar'],
                'ROAR': search_in(roar, data['repository_names']),
                'OAI-PMH': search_in(oai_pmh, data['repository_names']),
                're3data': result_pool['re3data']
            }
        },
        'collector': {
            'details': {
                'LA-Referencia': result_pool['LA-Referencia'],
                'OpenAIRE': result_pool['OpenAIRE'],
                'Google-Scholar': google_scholar(data['repository_url']),
                'BASE': result_pool['BASE'],
                'CORE': result_pool['CORE']
            }
        },
        'initiatives_existence': 1 if initiatives_existence else 0,
        'national_collector': count_national_collectors(form if national_collector else None),
        'url': friendly_secure_url(data['repository_url'])
    }
    dict_temp = resume_visibility['directory']['details'].copy()
    dict_temp.update(resume_visibility['collector']['details'])
    resume_visibility['standard'] = standard_name(dict_temp)
    resume_visibility['directory'].update(
        count_items(resume_visibility['directory']['details'], 'directorios internacionales'))
    resume_visibility['collector'].update(
        count_items(resume_visibility['collector']['details'], 'recolectores internacionales'))
    data_links = resume_visibility['directory']['details'].copy()
    data_links.update(resume_visibility['collector']['details'])
    resume_visibility['open_access'], links_dict = open_access(data_links)
    resume_visibility['total'] = sum(
        resume_visibility[i]['value'] if dict == type(resume_visibility[i]) else resume_visibility[i] for i in
        resume_visibility)
    return resume_visibility, links_dict
