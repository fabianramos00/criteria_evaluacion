from os.path import exists

from functools import wraps
from flask import Flask
from flask import request
from decouple import config

from scripts.visibility import *
from scripts.policy import *
from scripts.legal_aspects import *
from scripts.metadata import *
from scripts.forms import RegistrationForm, VisibilityForm, PolicyForm, LegalAspectsForm, MetadataForm
from scripts.tools import generate_token, ping, save_dict, load_dict, format_response
from models.models import db

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = config('DATABASE_URL')
# app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///db.sqlite3'
db.init_app(app)

criteria_list = ['visibility', 'policy', 'legal_aspects', 'metadata']

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        path_list = request.path.split('/')
        token, item = path_list[-1], path_list[1]
        if not exists(f'./data/{token}.json'):
            return {'error': 'Token inválido'}, 406
        data = load_dict(path_list[-1])
        if item in data:
            return {'error': 'El ítem ya fue evaluado'}, 406
        elif item != criteria_list[0] and criteria_list[criteria_list.index(item)-1] not in data:
            return {'error': 'No se ha evaluado el ítem previo'}, 406
        return f(*args, **kwargs)
    return decorated_function

def save_result(token, data, result, item):
    data.update({item: result})
    data['total'] += result['total']
    save_dict(token, data)
    result['accumulative'] = result['total']
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
    data['links'] =  links
    return save_result(token, data, result, 'metadata'), 200

if __name__ == '__main__':
    app.run(debug=True)
