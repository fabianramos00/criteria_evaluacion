import json
from os.path import exists
from uuid import uuid4
# from subprocess import check_output, CalledProcessError, STDOUT

from requests import get
from requests.exceptions import ConnectionError

def ping(host):
    try:
        request = get(host)
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
    response = get(url)
    return True if response.status_code == 200 else False

def save_dict(token, data):
    dump_data = json.dumps(data)
    f = open(f'./data/{token}.json', 'w')
    f.write(dump_data)
    f.close()

def load_dict(token):
    with open(f'./data/{token}.json') as json_file:
        return json.load(json_file)

def generate_token():
    flag, token = True, None
    while flag:
        token = uuid4()
        if not exists(f'./data/{token}.json'):
            flag = False
    return token
