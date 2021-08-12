from scripts.tools import count_form_boolean_fields

def execute_services(form, data):
    services_resume = count_form_boolean_fields(form)
    services_resume['total'] = sum(
        services_resume[i]['value'] if dict == type(services_resume[i]) else services_resume[i] for i in
        services_resume)
    return services_resume
