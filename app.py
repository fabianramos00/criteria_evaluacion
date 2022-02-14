from functools import wraps
from flask import Flask
from flask import request
from flask_cors import CORS
from decouple import config
from flask_migrate import Migrate
from sqlalchemy import desc
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from constants import CRITERIA_LIST, CRITERIA_ITEM_DICT
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
from scripts.tools import save_record, load_dict, format_response
from models.models import db, Record
from models.schemas import RecordSchema

disable_warnings(InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

app.config['CORS_HEADERS'] = 'Content-Type'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = config('DATABASE_URL')
# app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///db.sqlite3'
db.init_app(app)
migrate = Migrate(app, db)


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        path_list = request.path.split('/')
        token, item = path_list[-1], path_list[1]
        record = Record.query.filter_by(token=token).first()
        if record is None:
            return {'error': 'Token inválido'}, 406
        data = record.data
        if item in data:
            item_data = data[item]
            item_data['accumulative'] = data['total']
            return format_response(item_data, data), 200
        if item != CRITERIA_LIST[0] and CRITERIA_LIST[CRITERIA_LIST.index(item) - 1] not in data:
            return {'error': 'No se ha evaluado el ítem previo'}, 406
        return f(*args, **kwargs)

    return decorated_function


def clean_request_data(data=None, form=None, repository_url=None):
    for i in list(data):
        if 'url' not in i and not data[i] and i + '_url' in data:
            del data[i + '_url']
    if repository_url:
        data.update({'url': repository_url})
    return data, form.from_json(data)


def save_result(token, data, result, item):
    data.update({item: result})
    data['total'] += result['total']
    save_record(data, db, token, item == CRITERIA_LIST[-1], item)
    result['accumulative'] = data['total']
    return format_response(result, data)


@app.route('/', methods=['POST'])
def home():
    form = RegistrationForm.from_json(request.json)
    if not form.validate():
        return form.errors, 400
    data_repository = {
        'repository_url': form.repository_url.data,
        'repository_names': [form.repository_name.data],
        'total': 0
    }
    if form.repository_name1.data:
        data_repository['repository_names'].append(form.repository_name1.data)
    record = save_record(data_repository, db)
    return {'token': record.token}, 200


@app.route('/visibility/<token>', methods=['POST'])
@token_required
def visibility(token):
    visibility_json = request.json
    if not visibility_json['national_collector']:
        for key in list(visibility_json):
            if 'collector_url' in key:
                del visibility_json[key]
    visibility_form = VisibilityForm.from_json(request.json)
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
    request_dict, policy_form = clean_request_data(data=request.json, form=PolicyForm,
                                                   repository_url=data['repository_url'])
    if not policy_form.validate():
        return policy_form.errors, 400
    result = execute_policy(request_dict, data['repository_names'])
    return save_result(token, data, result, 'policy'), 200


@app.route('/legal_aspects/<token>', methods=['POST'])
@token_required
def legal_aspects(token):
    legal_aspects_json, legal_aspects_form = clean_request_data(data=request.json, form=LegalAspectsForm)
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
    request_dict, security_form = clean_request_data(data=request.json, form=SecurityForm,
                                                   repository_url=data['repository_url'])
    if not security_form.validate():
        return security_form.errors, 400
    result = execute_security(request_dict)
    return save_result(token, data, result, 'security'), 200


@app.route('/statistics/<token>', methods=['POST'])
@token_required
def statistics(token):
    data = load_dict(token)
    request_dict, statistics_form = clean_request_data(data=request.json, form=StatisticsForm,
                                                   repository_url=data['repository_url'])
    if not statistics_form.validate():
        return statistics_form.errors, 400
    result, links_dict = execute_statistics(request_dict, data['links'])
    data['links'] = links_dict
    return save_result(token, data, result, 'statistics'), 200


@app.route('/services/<token>', methods=['POST'])
@token_required
def services(token):
    data = load_dict(token)
    request_dict, services_form = clean_request_data(data=request.json, form=ServicesForm,
                                                   repository_url=data['repository_url'])
    if not services_form.validate():
        return services_form.errors, 400
    result = execute_services(request_dict, data['links'])
    return save_result(token, data, result, 'services'), 200


@app.route('/<item>/<token>', methods=['GET'])
def get_data(item, token):
    if item not in CRITERIA_LIST:
        return {'error': 'Item inválido'}, 400
    record = Record.query.filter_by(token=token).first()
    if record is None:
        return {'error': 'Token inválido'}, 400
    is_next = True if not record.is_completed and (
            (item == CRITERIA_LIST[0] and record.last_item_evaluated == 'started') or (
            item == CRITERIA_LIST[CRITERIA_LIST.index(record.last_item_evaluated) + 1])) else False
    if item not in record.data:
        return {'is_next': is_next, 'is_completed': False}, 404
    item_data = record.data[item]
    item_data['accumulative'] = record.data['total']
    response_data = format_response(item_data, record.data)
    response_data['is_next'], response_data['is_completed'] = is_next, True
    return response_data, 200


@app.route('/list', methods=['GET'])
def get_list():
    page = int(request.args.get('page')) if request.args.get('page') is not None else 1
    quantity = int(request.args.get('quantity')) if request.args.get('quantity') is not None else 10
    record_list = Record.query.order_by(desc(Record.last_updated)).paginate(page, quantity, error_out=False)
    record_schema = RecordSchema(many=True)
    return {
               'has_prev': record_list.has_prev,
               'has_next': record_list.has_next,
               'prev_num': record_list.prev_num,
               'next_num': record_list.next_num,
               'pages': record_list.pages,
               'total_records': record_list.total,
               'items': record_schema.dump(record_list.items)
           }, 200


@app.route('/summary/<token>', methods=['GET'])
def get_summary(token):
    record = Record.query.filter_by(token=token).first()
    if record is None:
        return {'error': 'Token inválido'}, 406
    record_schema = RecordSchema().dump(record)
    record_schema['summary'] = [{'item': i, 'total': record.data[i]['total'], 'item_name': CRITERIA_ITEM_DICT[i]} for i
                                in CRITERIA_LIST]
    return record_schema, 200


if __name__ == '__main__':
    app.run(debug=True)
