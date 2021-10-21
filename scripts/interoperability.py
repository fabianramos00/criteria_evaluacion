from constants import DOCUMENT_IDENTIFIER_LIST
from scripts.tools import count_form_boolean_fields

def check_collectors(data):
    value, text = 1, 'Presencia en los dos recolectores'
    if data['LA-Referencia'] is None and data['OpenAIRE'] is None:
        value, text = 0, 'No esta presente en los dos recolectores'
    elif data['LA-Referencia'] is None:
        value, text = 0, 'No esta presente en la LA Referencia'
    elif data['OpenAIRE'] is None:
        value, text = 0, 'No esta presente en la OpenAIRE'
    return {
        'value': value,
        'text': text
    }

def check_oai_pmh(oai_pmh_value):
    value, url = 0, None
    if oai_pmh_value is not None:
        value, url = 1, oai_pmh_value['host']
    return {
        'value': value,
        'url': url
    }

def check_identifier(links):
    if 0 < len(links):
        for i in links:
            value = i['metadata']['DC.identifier']
            if any(ext in value for ext in DOCUMENT_IDENTIFIER_LIST):
                pass
            else:
                return 0
        return 1
    return 0

def execute_interoperability(form, data):
    interoperability_resume = count_form_boolean_fields(form)
    interoperability_resume['collector'] = check_collectors(data['visibility']['collector']['details'])
    interoperability_resume['oai_pmh'] = check_oai_pmh(data['visibility']['directory']['details']['OAI-PMH'])
    interoperability_resume['headers_html'] = data['metadata']['dublin_core']
    interoperability_resume['standard_identifier'] = check_identifier(data['links'])
    interoperability_resume['total'] = sum(
        interoperability_resume[i]['value'] if dict == type(interoperability_resume[i]) else interoperability_resume[i] for i in
        interoperability_resume)
    return interoperability_resume
