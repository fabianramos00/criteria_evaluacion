from scripts.tools import count_form_boolean_fields

def execute_security(form):
    security_resume = count_form_boolean_fields(form)
    security_resume['total'] = sum(
        security_resume[i]['value'] if dict == type(security_resume[i]) else security_resume[i] for i in
        security_resume)
    return security_resume
