from scripts.tools import count_form_boolean_fields

def author_metadata(link_list):
    for link in link_list:
        if not link['author_rights']:
            return 0
    return 1

def execute_legal_aspects(form, link_list):
    legal_aspects_resume = count_form_boolean_fields(form)
    legal_aspects_resume['author_metadata'] = author_metadata(link_list)
    legal_aspects_resume['total'] = sum(
        legal_aspects_resume[i]['value'] if dict == type(legal_aspects_resume[i]) else legal_aspects_resume[i] for i in
        legal_aspects_resume)
    return legal_aspects_resume
