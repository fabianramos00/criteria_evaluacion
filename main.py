from os.path import exists

from functools import wraps
from flask import Flask
from flask import request
from flask_cors import CORS
from decouple import config
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from scripts.visibility import *
from scripts.policy import *
from scripts.legal_aspects import *
from scripts.metadata import *
from scripts.interoperability import *
from scripts.security import *
from scripts.statistics import *
from scripts.services import *
from scripts.forms import RegistrationForm, VisibilityForm, PolicyForm, LegalAspectsForm, MetadataForm, SecurityForm, \
    InteroperabilityForm, StatisticsForm, ServicesForm
from scripts.tools import generate_token, ping, save_dict, load_dict, format_response
from models.models import db

disable_warnings(InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = config('DATABASE_URL')
# app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///db.sqlite3'
db.init_app(app)

criteria_list = ['visibility', 'policy', 'legal_aspects', 'metadata', 'interoperability', 'security', 'statistics',
                 'services']

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        path_list = request.path.split('/')
        token, item = path_list[-1], path_list[1]
        if not exists(f'./data/{token}.json'):
            return {'error': 'Token inválido'}, 406
        data = load_dict(path_list[-1])
        # if item in data:
        #     return {'error': 'El ítem ya fue evaluado'}, 406
        if item != criteria_list[0] and criteria_list[criteria_list.index(item) - 1] not in data:
            return {'error': 'No se ha evaluado el ítem previo'}, 406
        return f(*args, **kwargs)
    return decorated_function

def save_result(token, data, result, item):
    data.update({item: result})
    data['total'] += result['total']
    save_dict(token, data)
    result['accumulative'] = data['total']
    return format_response(result)

@app.route('/', methods=['POST'])
def home():
    form = RegistrationForm.from_json(request.json)
    if not form.validate():
        return form.errors, 400
    token = generate_token()
    data_repository = {
        'repository_url': form.repository_url.data,
        'repository_names': [form.repository_name.data],
        'total': 0
    }
    if form.repository_name1.data:
        data_repository['repository_names'].append(form.repository_name1.data)
    if form.repository_name2.data:
        data_repository['repository_names'].append(form.repository_name2.data)
    save_dict(token, data_repository)
    return {'token': token}, 200

@app.route('/visibility/<token>', methods=['POST'])
@token_required
def visibility(token):
    visibility_json, visibility_form = request.json, VisibilityForm.from_json(request.json)
    if not visibility_form.validate():
        return visibility_form.errors, 400
    data = load_dict(token)
    result, links_dict = execute_visibility(data, visibility_json)
    data['links'] = links_dict
    return save_result(token, data, result, 'visibility'), 200

@app.route('/policy/<token>', methods=['POST'])
@token_required
def policy(token):
    data = load_dict(token)
    request_dict = request.json
    request_dict.update({'url': data['repository_url']})
    policy_form = PolicyForm.from_json(request_dict)
    if not policy_form.validate():
        return policy_form.errors, 400
    result = execute_policy(request_dict, data['repository_names'])
    return save_result(token, data, result, 'policy'), 200

@app.route('/legal_aspects/<token>', methods=['POST'])
@token_required
def legal_aspects(token):
    legal_aspects_json, legal_aspects_form = request.json, LegalAspectsForm.from_json(request.json)
    if not legal_aspects_form.validate():
        return legal_aspects_form.errors, 400
    data = load_dict(token)
    result = execute_legal_aspects(legal_aspects_json, data['links'])
    return save_result(token, data, result, 'legal_aspects'), 200

@app.route('/metadata/<token>', methods=['POST'])
@token_required
def metadata(token):
    metadata_json, metadata_form = request.json, MetadataForm.from_json(request.json)
    if not metadata_form.validate():
        return metadata_form.errors, 400
    data = load_dict(token)
    result, links = execute_metadata(metadata_json, data['links'])
    data['links'] = links
    return save_result(token, data, result, 'metadata'), 200

@app.route('/interoperability/<token>', methods=['POST'])
@token_required
def interoperability(token):
    data = load_dict(token)
    interoperability_form = InteroperabilityForm.from_json(request.json)
    if not interoperability_form.validate():
        return interoperability_form.errors, 400
    result = execute_interoperability(request.json, data)
    return save_result(token, data, result, 'interoperability'), 200

@app.route('/security/<token>', methods=['POST'])
@token_required
def security(token):
    data = load_dict(token)
    request_dict = request.json
    request_dict.update({'url': data['repository_url']})
    security_form = SecurityForm.from_json(request_dict)
    if not security_form.validate():
        return security_form.errors, 400
    result = execute_security(request_dict)
    return save_result(token, data, result, 'security'), 200

@app.route('/statistics/<token>', methods=['POST'])
@token_required
def statistics(token):
    data = load_dict(token)
    request_dict = request.json
    request_dict.update({'url': data['repository_url']})
    statistics_form = StatisticsForm.from_json(request_dict)
    if not statistics_form.validate():
        return statistics_form.errors, 400
    result, links_dict = execute_statistics(request_dict, data['links'])
    data['links'] = links_dict
    return save_result(token, data, result, 'statistics'), 200

@app.route('/services/<token>', methods=['POST'])
@token_required
def services(token):
    data = load_dict(token)
    request_dict = request.json
    request_dict.update({'url': data['repository_url']})
    services_form = ServicesForm.from_json(request_dict)
    if not services_form.validate():
        return services_form.errors, 400
    result = execute_services(request_dict, data['links'])
    return save_result(token, data, result, 'services'), 200

@app.route('/<item>/<token>', methods=['GET'])
def get_data(item, token):
    if item not in criteria_list:
        return {'error': 'Item inválido'}, 400
    if not exists(f'./data/{token}.json'):
        return {'error': 'Token inválido'}, 400
    data = load_dict(token)
    if item not in data:
        return {'error': 'El item no ha sido evaluado'}, 404
    item_data = data[item]
    item_data['accumulative'] = data['total']
    return format_response(item_data), 200

if __name__ == '__main__':
    app.run(debug=True)
