from concurrent.futures import ThreadPoolExecutor

from requests import get

from scripts.tools import count_form_boolean_fields

def statistics_url_exist(url):
    try:
        response = get(url + '/statistics')
        if response.status_code < 400:
            return url + '/statistics'
        return None
    except ConnectionError:
        return None

def evaluate_urls_statistics(url_list):
    result = {'value': 1 if 0 < len(url_list) else 0, 'details': []}
    with ThreadPoolExecutor(max_workers=3) as executor:
        for i in url_list:
            i['statistics'] = executor.submit(statistics_url_exist, i['url']).result()
            if i['statistics'] is None:
                result['value'] = 0
                result['details'].append(i['url'])
    return result

def execute_statistics(form, url_list):
    statistics_resume = count_form_boolean_fields(form)
    statistics_resume['url_statistics'] = evaluate_urls_statistics(url_list)
    statistics_resume['total'] = sum(
        statistics_resume[i]['value'] if dict == type(statistics_resume[i]) else statistics_resume[i] for i in
        statistics_resume)
    return statistics_resume, url_list
