def author_metadata(link_list):
    for link in link_list:
        if not link['author_rights']:
            return 0
    return 1

def execute_legal_aspects(form, link_list):
    field_list_url = [x for x in form if '_url' not in x and x + '_url' in form]
    field_list = [x for x in form if '_url' not in x and x + '_url' not in form]
    legal_aspects_resume = {}
    for i in field_list_url:
        legal_aspects_resume[i] = {
            'value': 1 if form[i] else 0,
            'url': form[i + '_url'] if form[i] else None
        }
    for i in field_list:
        legal_aspects_resume[i] = 1 if form[i] else 0
    legal_aspects_resume['author_metadata'] = author_metadata(link_list)
    legal_aspects_resume['total'] = sum(
        legal_aspects_resume[i]['value'] if dict == type(legal_aspects_resume[i]) else legal_aspects_resume[i] for i in
        legal_aspects_resume)
    return legal_aspects_resume
