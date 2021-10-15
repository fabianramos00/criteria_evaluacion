import json
from os.path import exists
from uuid import uuid4
# from subprocess import check_output, CalledProcessError, STDOUT

from requests import get
from requests.exceptions import ConnectionError

from models.models import Record


def ping(host):
    try:
        request = get(host, verify=False)
        return True
    except ConnectionError:
        return False


# def ping(host):
# host = host.replace('https://', '').replace('http://', '')
# try:
#     param = '-n' if platform.system().lower() == 'windows' else '-c'
#     check_output(
#         ['ping', param, '3', host],
#         stderr=STDOUT,
#         universal_newlines=True,
#         shell=False
#     )
#     return True
# except CalledProcessError:
#     return False

def check_website(url):
    response = get(url, verify=False)
    return True if response.status_code == 200 else False


def save_record(data, db, token=None, is_completed=False, last_item_evaluated=''):
    record = None
    if token is not None:
        record = Record.query.filter_by(token=token).first()
    if record is None:
        record = Record(data, data['repository_url'], data['repository_names'])
        db.session.add(record)
    else:
        record.data, record.rating, record.is_completed, record.last_item_evaluated = data, data[
            'total'], is_completed, last_item_evaluated
    db.session.commit()
    return record


def load_dict(token):
    return Record.query.filter_by(token=token).first().data


def format_response(result_dict):
    for i in result_dict:
        if type(result_dict[i]) == dict:
            if 'text' in result_dict[i]:
                actual_result = result_dict[i]
                result_dict[i] = {
                    'text': actual_result['text'],
                    'value': actual_result['value'],
                }
                if 'details' in actual_result:
                    result_dict[i]['details'] = [x for x in actual_result['details'] if
                                                 actual_result['details'][x] is None]
            elif 'url' in result_dict[i]:
                result_dict[i] = result_dict[i]['value']
    return result_dict


def count_form_boolean_fields(dict_form):
    if 'url' in dict_form:
        del dict_form['url']
    field_list_url = [x for x in dict_form if '_url' not in x and x + '_url' in dict_form]
    field_list = [x for x in dict_form if '_url' not in x and x + '_url' not in dict_form]
    resume = {}
    for i in field_list_url:
        resume[i] = {
            'value': 1 if dict_form[i] else 0,
            'url': dict_form[i + '_url'] if dict_form[i] else None
        }
    for i in field_list:
        resume[i] = 1 if dict_form[i] else 0
    return resume
