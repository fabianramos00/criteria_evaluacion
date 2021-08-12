from scripts.tools import count_form_boolean_fields

def check_collectors(data):
    value, text = 1, 'Presencia en los dos recolectores'
    if data['collector']['LA-Referencia'] is None:
        value, text = 0, 'No esta presente en la LA Referencia'
    if data['collector']['LA-Referencia'] is None:
        value, text = 0, 'No esta presente en la LA Referencia'
    return {
        'value': value,
        'text': text
    }

def execute_interoperability(form, data):
    interoperability_resume = count_form_boolean_fields(form)
    interoperability_resume['collector'] = check_collectors(data)
    interoperability_resume['headers_html'] = 1 if data['dublin_core'] is not None else 0
    interoperability_resume['total'] = sum(
        interoperability_resume[i]['value'] if dict == type(interoperability_resume[i]) else interoperability_resume[i] for i in
        interoperability_resume)
    return interoperability_resume, data
