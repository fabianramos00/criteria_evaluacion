from wtforms import Form, StringField, BooleanField
from wtforms.validators import DataRequired, URL, Optional, InputRequired, ValidationError
import wtforms_json

from scripts.tools import ping, check_website

wtforms_json.init()

def domain_valid(form, field):
    if field.data is not None and not ping(field.data):
        field.errors.append('No es posible acceder a la página')
        return False

def boolean_required(form, field):
    if 0 == len(field.raw_data):
        field.errors.append('El campo es requerido')
        return False
    if type(field.raw_data[0]) != bool:
        field.errors.append('El campo es inválido')
        return False

def website_valid(form, field):
    if field.data is not None and not check_website(field.data):
        field.errors.append('No es posible acceder a la página')
        return False

class CompareUrl(object):

    def __init__(self, field_name):
        self.field_name = field_name

    def __call__(self, form, field):
        url_field = form[self.field_name]
        if field.data is not None and url_field.data not in field.data:
            raise ValidationError('La URL ingresada no concuerda con la URL del repositorio')

class RequiredIf(DataRequired):

    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name
        super(RequiredIf, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form[self.other_field_name]
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if other_field.data:
            # super(RequiredIf, self).__call__(form, field)
            DataRequired.__call__(self, form, field)
        Optional()(form, field)

class RegistrationForm(Form):
    repository_url = StringField('URL', validators=[DataRequired('El campo es requerido'), URL(message='URL inválida'), domain_valid])
    repository_name = StringField('Nombre', validators=[DataRequired('El campo es requerido')])
    repository_name1 = StringField('Nombre 1')
    repository_name2 = StringField('Nombre 2')

    def validate(self):
        if not super(RegistrationForm, self).validate():
            return False
        if self.repository_name.data and self.repository_name1.data and self.repository_name.data == self.repository_name1.data:
            msg = 'Los nombres ingresados están repetidos'
            self.repository_name.errors.append(msg)
            self.repository_name1.errors.append(msg)
            return False
        if self.repository_name.data and self.repository_name1.data and self.repository_name.data == self.repository_name2.data:
            msg = 'Los nombres ingresados están repetidos'
            self.repository_name.errors.append(msg)
            self.repository_name2.errors.append(msg)
            return False
        if self.repository_name1.data and self.repository_name2.data and self.repository_name1.data == self.repository_name2.data:
            msg = 'Los nombres ingresados están repetidos'
            self.repository_name1.errors.append(msg)
            self.repository_name2.errors.append(msg)
            return False
        return True

class VisibilityForm(Form):
    national_collector = BooleanField('Presencia en recolectores nacionales', validators=[boolean_required])
    initiatives_existence = BooleanField('Existencia de iniciativas', validators=[boolean_required])
    collector_url1 = StringField('URL_1', validators=[RequiredIf('national_collector', message='El campo es requerido'), URL(message='URL inválida'), domain_valid])
    collector_url2 = StringField('URL_2', validators=[Optional(), URL(message='URL inválida'), domain_valid])
    collector_url3 = StringField('URL_3', validators=[Optional(), URL(message='URL inválida'), domain_valid])
    collector_url4 = StringField('URL_4', validators=[Optional(), URL(message='URL inválida'), domain_valid])
    collector_url5 = StringField('URL_5', validators=[Optional(), URL(message='URL inválida'), domain_valid])

class PolicyForm(Form):
    open_access = BooleanField(validators=[boolean_required])
    open_access_url = StringField(validators=[RequiredIf('open_access', message='El campo es requerido'), URL(message='URL inválida'), website_valid])
    metadata_reuse = BooleanField(validators=[boolean_required])
    metadata_reuse_url = StringField(validators=[RequiredIf('metadata_reuse', message='El campo es requerido'), URL(message='URL inválida'), website_valid])
    content_preservation = BooleanField(validators=[boolean_required])
    content_preservation_url = StringField(validators=[RequiredIf('content_preservation', message='El campo es requerido'), URL(message='URL inválida'), website_valid])
    deposit_data = BooleanField(validators=[boolean_required])
    deposit_data_url = StringField(validators=[RequiredIf('deposit_data', message='El campo es requerido'), URL(message='URL inválida'), website_valid])
    action_policy = BooleanField(validators=[boolean_required])
    action_policy_url = StringField(validators=[RequiredIf('action_policy', message='El campo es requerido'), URL(message='URL inválida'), website_valid, CompareUrl('url')])
    policy_data = BooleanField(validators=[boolean_required])
    policy_data_url = StringField(validators=[RequiredIf('policy_data', message='El campo es requerido'), URL(message='URL inválida'), website_valid, CompareUrl('url')])
    vision_mission = BooleanField(validators=[boolean_required])
    vision_mission_url = StringField(validators=[RequiredIf('vision_mission', message='El campo es requerido'), URL(message='URL inválida'), website_valid, CompareUrl('url')])
    contact = BooleanField(validators=[boolean_required])
    contact_url = StringField(validators=[RequiredIf('contact', message='El campo es requerido'), URL(message='URL inválida'), website_valid, CompareUrl('url')])
    url = StringField()

class LegalAspectsForm(Form):
    author_property = BooleanField(validators=[boolean_required])
    author_permission = BooleanField(validators=[boolean_required])
    author_permission_url = StringField(validators=[RequiredIf('author_permission', message='El campo es requerido'), URL(message='URL inválida'), website_valid])
    editorial_policy = BooleanField(validators=[boolean_required])
    author_copyright = BooleanField(validators=[boolean_required])

class MetadataForm(Form):
    curation = BooleanField(validators=[boolean_required])

class InteroperabilityForm(Form):
    deleted_records = BooleanField(validators=[boolean_required])
    life_time = BooleanField(validators=[boolean_required])
    admin_email = BooleanField(validators=[boolean_required])
    identify_description = BooleanField(validators=[boolean_required])
    progressive_delivery = BooleanField(validators=[boolean_required])
    records_size = BooleanField(validators=[boolean_required])
    records_datestamp = BooleanField(validators=[boolean_required])
    systems_integration = BooleanField(validators=[boolean_required])
    share_data = BooleanField(validators=[boolean_required])

class SecurityForm(Form):
    backups = BooleanField(validators=[boolean_required])
    backups_url = StringField(validators=[RequiredIf('backups', message='El campo es requerido'), URL(message='URL inválida'), website_valid, CompareUrl('url')])
    checksum = BooleanField(validators=[boolean_required])
    checksum_url = StringField(validators=[RequiredIf('checksum', message='El campo es requerido'), URL(message='URL inválida'), website_valid, CompareUrl('url')])
    backups_location = BooleanField(validators=[boolean_required])
    format_control = BooleanField(validators=[boolean_required])
    url = StringField()

class StatisticsForm(Form):
    general_statistics = BooleanField(validators=[boolean_required])
    general_statistics_url = StringField(validators=[RequiredIf('general_statistics', message='El campo es requerido'), URL(message='URL inválida'), website_valid, CompareUrl('url')])
    save_logs = BooleanField(validators=[boolean_required])
    counter = BooleanField(validators=[boolean_required])
    url = StringField()

class ServicesForm(Form):
    rss_alert = BooleanField(validators=[boolean_required])
    author_profiles = BooleanField(validators=[boolean_required])
    author_profiles_url = StringField(validators=[RequiredIf('author_profiles', message='El campo es requerido'), URL(message='URL inválida'), website_valid, CompareUrl('url')])
    cite_metrics = BooleanField(validators=[boolean_required])
    cite_metrics_url = StringField(validators=[RequiredIf('cite_metrics', message='El campo es requerido'), URL(message='URL inválida'), website_valid, CompareUrl('url')])
    new_metrics = BooleanField(validators=[boolean_required])
    new_metrics_url = StringField(validators=[RequiredIf('new_metrics', message='El campo es requerido'), URL(message='URL inválida'), website_valid, CompareUrl('url')])
    url = StringField()