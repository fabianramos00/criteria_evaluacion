CRITERIA_LIST = ['visibility', 'policy', 'legal_aspects', 'metadata', 'interoperability', 'security', 'statistics',
                 'services']

CRITERIA_ITEM_DICT = {'started': 'Iniciada', 'visibility': 'Visibilidad', 'policy': 'Políticas',
                      'legal_aspects': 'Aspectos legales',
                      'metadata': 'Metadatos', 'interoperability': 'Interoperabilidad', 'security': 'Seguridad',
                      'statistics': 'Estadísticas',
                      'services': 'Servicios'}

METADATA_FIELDS = ['DC.creator', 'DC.title', 'DC.type', 'DC.rights', 'DC.description', 'DC.format',
                   'DC.language', 'DC.identifier', 'DC.subject', 'DC.contributor', 'DC.relation', 'DC.publisher']

FIELDS_ITEM = ['standard_access_value', 'standard_date_format', 'standard_type_research_result',
               'single_type_research_result', 'standard_format', 'standard_version_coar', 'single_version',
               'standard_language', 'dublin_core', 'author_id']

ACCESS_STANDARD_VALUES = ['closedAccess', 'embargoedAccess', 'openAccess', 'restrictedAccess']

RESULT_TYPES = ['article', 'bachelorThesis', 'masterThesis', 'doctoralThesis', 'book', 'bookPart', 'review',
                'conferenceObject', 'lecture', 'workingPaper', 'preprint', 'report', 'annotation',
                'contributionToPeriodical', 'patent', 'other']

VERSION_COAR_LIST = ['draft', 'submittedVersion', 'acceptedVersion', 'publishedVersion', 'updatedVersion']

FORMAT_DICT = {
    'text': ['plain', 'richtext', 'enriched', 'tab-separated-values', 'html', 'sgml', 'xml'],
    'application': ['octet-stream', 'postscript', 'rtf', 'applefile', 'mac-binhex40', 'wordperfect5.1', 'pdf',
                    'vnd.oasis.opendocument.text', 'zip', 'macwriteii', 'msword', 'sgml', 'ms-excel', 'ms-powerpoint',
                    'ms-project', 'ms-works', 'xhtml+xml', 'xml'],
    'image': ['jpeg', 'gif', 'tiff', 'png', 'jpeg2000', 'sid'],
    'audio': ['wav', 'mp3', 'quicktime'],
    'video': ['mpeg1', 'mpeg2', 'mpeg3', 'av']
}

BIBLIOGRAPHIC_MANAGERS = ['mendeley', 'zotero']

METADATA_EXPORT_TYPES = ['mets', 'premis', 'rdf', 'json', 'marc', 'bibtex']

SOCIAL_NETWORKS = ['facebook', 'twitter', 'linkedin']

METADATA_DATE_REGEX = [r'DC.date.*', r'DCTERMS.date.*']

DATE_FORMATS = ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%SZ']

ISO_LANGUAGE_LIST = [('part3', 'ISO 639-3'), ('part2b', 'ISO 639-2'), ('part2t', 'ISO 639-2'), ('part1', 'ISO 639-1')]

IRALIS_BASE_URL_ID = 'https://www.iralis.org/'

ORCID_BASE_URL_ID = 'https://orcid.org/'

DOCUMENT_IDENTIFIER_LIST = ['doi', 'handle', 'urn', 'orcid']