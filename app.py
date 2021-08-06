from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from scripts.visibility import *
from scripts.policy import *
from scripts.legal_aspects import *
from scripts.metadata import *
from flask import request
from os.path import exists

from scripts.forms import RegistrationForm, VisibilityForm, PolicyForm, LegalAspectsForm, MetadataForm
from scripts.tools import generate_token, ping, save_dict, load_dict

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://root:root1@localhost/criteria'
# app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///db.sqlite3'
db = SQLAlchemy(app)

@app.route('/', methods=['POST'])
def home():
    form = RegistrationForm.from_json(request.json)
    if not form.validate():
        return form.errors, 400
    token = generate_token()
    data_repository = {
        'repository_url': form.repository_url.data,
        'repository_names': [form.repository_name.data]
    }
    if form.repository_name1.data:
        data_repository['repository_names'].append(form.repository_name1.data)
    if form.repository_name2.data:
        data_repository['repository_names'].append(form.repository_name2.data)
    save_dict(token, data_repository)
    return {'token': token}, 200

@app.route('/visibility/<token>', methods=['POST'])
def visibility(token):
    if not exists(f'./data/{token}.json'):
        return {'error': 'Token inválido'}, 406
    visibility_json, visibility_form = request.json, VisibilityForm.from_json(request.json)
    if not visibility_form.validate():
        return visibility_form.errors, 400
    data = load_dict(token)
    result, links_dict = execute_visibility(data, visibility_json)
    data.update({'visibility': result})
    data['links'] = links_dict
    data['total'] = result['total']
    save_dict(token, data)
    result['accumulative'] = result['total']
    return result, 200

@app.route('/policy/<token>', methods=['POST'])
def policy(token):
    if not exists(f'./data/{token}.json'):
        return {'error': 'Token inválido'}, 406
    data = load_dict(token)
    request_dict = request.json
    request_dict.update({'url': data['repository_url']})
    policy_form = PolicyForm.from_json(request_dict)
    if not policy_form.validate():
        return policy_form.errors, 400
    result = execute_policy(request_dict, data['repository_names'])
    data.update({'policy': result})
    data['total'] += result['total']
    save_dict(token, data)
    result['accumulative'] = data['total']
    return result, 200

@app.route('/legal_aspects/<token>', methods=['POST'])
def legal_aspects(token):
    if not exists(f'./data/{token}.json'):
        return {'error': 'Token inválido'}, 406
    legal_aspects_json, legal_aspects_form = request.json, LegalAspectsForm.from_json(request.json)
    if not legal_aspects_form.validate():
        return legal_aspects_form.errors, 400
    data = load_dict(token)
    result = execute_legal_aspects(legal_aspects_json, data['links'])
    data.update({'legal_aspects': result})
    data['total'] += result['total']
    save_dict(token, data)
    result['accumulative'] = data['total']
    return result, 200

@app.route('/metadata/<token>', methods=['POST'])
def metadata(token):
    if not exists(f'./data/{token}.json'):
        return {'error': 'Token inválido'}, 406
    metadata_json, metadata_form = request.json, MetadataForm.from_json(request.json)
    if not metadata_form.validate():
        return metadata_form.errors, 400
    data = load_dict(token)
    result = execute_metadata(metadata_json, data['links'])
    # data.update({'legal_aspects': result})
    # data['total'] += result['total']
    # save_dict(token, data)
    # result['accumulative'] = data['total']
    return result, 200
    # return {'result': result}, 200

if __name__ == '__main__':
    app.run(debug=True)
