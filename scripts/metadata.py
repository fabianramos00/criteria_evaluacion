from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from bs4 import BeautifulSoup
from iso639 import languages
from requests import get
from re import compile

from constants import METADATA_DATE_REGEX, DATE_FORMATS, ACCESS_STANDARD_VALUES, RESULT_TYPES, FORMAT_DICT, \
    VERSION_COAR_LIST, ISO_LANGUAGE_LIST, IRALIS_BASE_URL_ID, ORCID_BASE_URL_ID, METADATA_FIELDS, \
    BIBLIOGRAPHIC_MANAGERS, METADATA_EXPORT_TYPES, SOCIAL_NETWORKS, FIELDS_ITEM
from scripts.tools import count_form_boolean_fields


def check_metadata_date(page_parse):
    date_dict = {}
    standard_date_format = True
    for regex in METADATA_DATE_REGEX:
        metadata_date = page_parse.find_all('meta', {'name': compile(regex)})
        for i in metadata_date:
            date_dict[i['name']] = i['content']
            if standard_date_format:
                standard_date_format = False
                for x in DATE_FORMATS:
                    try:
                        datetime.strptime(i['content'], x)
                        standard_date_format = True
                        break
                    except ValueError:
                        pass
    return (date_dict if date_dict else None), (standard_date_format if standard_date_format else None)


def check_access_name(name_list):
    if name_list is not None:
        for i in name_list:
            access_value = [x for x in ACCESS_STANDARD_VALUES if x in i]
            if 0 < len(access_value):
                return access_value[0]
    return None


def check_types_research_result(metadata):
    if metadata is not None:
        values = []
        for i in metadata:
            for j in RESULT_TYPES:
                if j in i:
                    values.append(i)
                    break
        return values if 0 < len(values) else None
    return None


def check_format(format_content):
    if format_content is not None:
        if type(format_content) != list:
            format_content = [format_content]
        for i in format_content:
            values = i.split('/')
            if len(values) == 2:
                if values[0] in FORMAT_DICT and values[1] in FORMAT_DICT[values[0]]:
                    return i
    return None


def check_version_format(metadata):
    if metadata is not None:
        values = []
        for i in metadata:
            for j in VERSION_COAR_LIST:
                if j in i:
                    values.append(i)
                    break
        return values if 0 < len(values) else None
    return None


def check_language_format(language_value):
    if language_value is not None:
        for i, j in ISO_LANGUAGE_LIST:
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
                if IRALIS_BASE_URL_ID in i or ORCID_BASE_URL_ID in i:
                    pass
                else:
                    return None
            return 'ORCID/IraLIS'
        else:
            if IRALIS_BASE_URL_ID in author_value:
                return 'IraLIS'
            if ORCID_BASE_URL_ID in author_value:
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
    for name in METADATA_FIELDS:
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
        'bibliographic_managers': search_items(BIBLIOGRAPHIC_MANAGERS, page_parse),
        'metadata_exports': search_items(METADATA_EXPORT_TYPES, page_parse),
        'social_networks': search_items(SOCIAL_NETWORKS, page_parse)
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
    fields_metadata, item_fields = METADATA_FIELDS.copy(), FIELDS_ITEM.copy()
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
    with ThreadPoolExecutor(max_workers=3) as executor:
        new_link_list = [executor.submit(get_metadata, x).result() for x in link_list]
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
