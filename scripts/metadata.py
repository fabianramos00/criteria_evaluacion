from datetime import datetime

from bs4 import BeautifulSoup
from iso639 import languages
from requests import get
from re import compile

from scripts.tools import count_form_boolean_fields

metadata_fields = ['DC.creator', 'DC.title', 'DC.type', 'DC.rights', 'DC.description', 'DC.format',
                   'DC.language', 'DC.identifier', 'DC.subject', 'DC.contributor', 'DC.relation', 'DC.publisher']
fields_item = ['standard_access_value', 'standard_date_format', 'standard_type_research_result',
               'single_type_research_result', 'standard_format', 'standard_version_coar', 'single_version',
               'standard_language', 'dublin_core', 'author_id']

access_standard_values = ['closedAccess', 'embargoedAccess', 'openAccess', 'restrictedAccess']
result_types = ['article', 'bachelorThesis', 'masterThesis', 'doctoralThesis', 'book', 'bookPart', 'review',
                'conferenceObject', 'lecture', 'workingPaper', 'preprint', 'report', 'annotation',
                'contributionToPeriodical', 'patent', 'other']
version_coar_list = ['draft', 'submittedVersion', 'acceptedVersion', 'publishedVersion', 'updatedVersion']
format_dict = {
    'text': ['plain', 'richtext', 'enriched', 'tab-separated-values', 'html', 'sgml', 'xml'],
    'application': ['octet-stream', 'postscript', 'rtf', 'applefile', 'mac-binhex40', 'wordperfect5.1', 'pdf',
                    'vnd.oasis.opendocument.text', 'zip', 'macwriteii', 'msword', 'sgml', 'ms-excel', 'ms-powerpoint',
                    'ms-project', 'ms-works', 'xhtml+xml', 'xml'],
    'image': ['jpeg', 'gif', 'tiff', 'png', 'jpeg2000', 'sid'],
    'audio': ['wav', 'mp3', 'quicktime'],
    'video': ['mpeg1', 'mpeg2', 'mpeg3', 'av']
}
bibliographic_managers = ['mendeley', 'zotero']
metadata_export_types = ['mets', 'premis', 'rdf', 'json', 'marc', 'bibtex']

def check_metadata_date(page_parse):
    date_regex, date_formats, date_dict = [r'DC.date.*', r'DCTERMS.date.*'], ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%SZ'], {}
    standard_date_format = True
    for regex in date_regex:
        metadata_date = page_parse.find_all('meta', {'name': compile(regex)})
        for i in metadata_date:
            date_dict[i['name']] = i['content']
            if standard_date_format:
                standard_date_format = False
                for x in date_formats:
                    try:
                        datetime.strptime(i['content'], x)
                        standard_date_format = True
                    except ValueError:
                        pass
    return (date_dict if date_dict else None), (standard_date_format if standard_date_format else None)

def check_access_name(name_list):
    if name_list is not None:
        for i in name_list:
            access_value = [x for x in access_standard_values if x in i]
            if 0 < len(access_value):
                return access_value[0]
    return None

def check_types_research_result(metadata):
    if metadata is not None:
        values = []
        for i in metadata:
            for j in result_types:
                if j in i:
                    values.append(i)
                    break
        return values if 0 < len(values) else None
    return None

def check_format(format_content):
    if format_content is not None:
        values = format_content.split('/')
        if len(values) == 2:
            if values[0] in format_dict and values[1] in format_dict[values[0]]:
                return format_content
    return None

def check_version_format(metadata):
    if metadata is not None:
        values = []
        for i in metadata:
            for j in version_coar_list:
                if j in i:
                    values.append(i)
                    break
        return values if 0 < len(values) else None
    return None

def check_language_format(language_value):
    if language_value is not None:
        iso_list = [('part3', 'ISO 639-3'), ('part2b', 'ISO 639-2'), ('part2t', 'ISO 639-2'), ('part1', 'ISO 639-1')]
        for i, j in iso_list:
            try:
                languages.get(**{i: language_value})
                return j
            except KeyError:
                pass
        if 'zxx' == language_value:
            return 'zxx'
    return None

def check_author_id(author_value):
    if author_value is not None:
        if type(author_value) == list:
            for i in author_value:
                if 'https://www.iralis.org/' in i or 'https://orcid.org/' in i:
                    pass
                else:
                    return None
            return 'ORCID/IraLIS'
        else:
            if 'https://www.iralis.org/' in author_value:
                return 'IraLIS'
            if 'https://orcid.org/' in author_value:
                return 'ORCID'
    return None

def search_items(items, page):
    result = {i: None for i in items}
    links, value, items = page.find_all('a'), None, items.copy()
    for a in links:
        img_item = a.find('img')
        for i in items:
            if a.has_attr('href') and i in a['href']:
                value = a['href']
            elif i in a.text.lower():
                value = a.text
            elif img_item is not None and i in img_item['src']:
                value = img_item['src']
            if value is not None:
                result[i] = value
                items.remove(i)
                value = None
                break
    return result

def get_metadata(url_dict):
    page = get(url_dict['url'], verify=False)
    page_parse = BeautifulSoup(page.content, 'html.parser')
    metadata = {}
    for name in metadata_fields:
        meta_list = page_parse.find_all('meta', {'name': name})
        if len(meta_list) < 2:
            metadata[name] = meta_list[0]['content'] if 1 == len(meta_list) else None
        else:
            metadata[name] = [i['content'] for i in meta_list]
    meta_identifier = page_parse.find_all('meta', {'name': 'DC.identifier', 'scheme': 'DCTERMS.URI'})
    metadata['DC.identifier'] = meta_identifier[0]['content'] if 1 == len(meta_identifier) else None
    url_dict.update({
        'dublin_core': True if 0 < len(page_parse.find_all('meta', {'name': compile(r'DC..*')})) else None,
        'standard_access_value': check_access_name(metadata['DC.rights']),
        'standard_type_research_result': check_types_research_result(metadata['DC.type']),
        'standard_format': check_format(metadata['DC.format']),
        'standard_version_coar': check_version_format(metadata['DC.type']),
        'standard_language': check_language_format(metadata['DC.language']),
        'author_id': check_author_id(metadata['DC.creator']),
        'bibliographic_managers': search_items(bibliographic_managers, page_parse),
        'metadata_exports': search_items(metadata_export_types, page_parse)
    })
    metadata['DC.date'], url_dict['standard_date_format'] = check_metadata_date(page_parse)
    url_dict['single_type_research_result'] = url_dict['standard_type_research_result'][0] if url_dict[
                                                                                                  'standard_type_research_result'] is not None and len(
        url_dict[
            'standard_type_research_result']) == 1 else None
    url_dict['single_version'] = url_dict['standard_version_coar'][0] if url_dict[
                                                                             'standard_version_coar'] is not None and len(
        url_dict['standard_version_coar']) == 1 else None
    url_dict['metadata'] = metadata
    return url_dict

def validate_metadata(url_dict_list):
    fields_metadata_dict, fields_dict = {}, {}
    fields_metadata, item_fields = metadata_fields.copy(), fields_item.copy()
    fields_metadata.append('DC.date')
    for i in fields_metadata:
        fields_metadata_dict[i] = True
    for i in item_fields:
        fields_dict[i] = 1
    for url_dict in url_dict_list:
        for i in fields_metadata:
            if url_dict['metadata'][i] is None:
                fields_metadata_dict[i] = False
                fields_metadata.remove(i)
        for j in item_fields:
            if url_dict[j] is None:
                fields_dict[j] = 0
                item_fields.remove(j)
        if len(item_fields) == 0 and len(fields_metadata) == 0:
            break
    return fields_metadata_dict, fields_dict

def evaluate_metadata_group(metadata_dict, fields):
    new_dict = {'value': 1, 'details': {}}
    for i in fields:
        new_dict['details'][i] = metadata_dict[i]
        if not metadata_dict[i]:
            new_dict['value'] = 0
    return new_dict

def execute_metadata(form, link_list):
    metadata_resume = count_form_boolean_fields(form)
    new_link_list = [get_metadata(x) for x in link_list]
    result_metadata, result_fields = validate_metadata(new_link_list)
    metadata_resume['first_fields'] = evaluate_metadata_group(result_metadata,
                                                              ['DC.creator', 'DC.title', 'DC.type', 'DC.date',
                                                               'DC.rights'])
    metadata_resume['second_fields'] = evaluate_metadata_group(result_metadata,
                                                               ['DC.description', 'DC.format', 'DC.language',
                                                                'DC.identifier', 'DC.subject', 'DC.contributor',
                                                                'DC.relation', 'DC.publisher'])
    metadata_resume.update(result_fields)
    metadata_resume['total'] = sum(
        metadata_resume[i]['value'] if dict == type(metadata_resume[i]) else metadata_resume[i] for i in
        metadata_resume)
    return metadata_resume, new_link_list
