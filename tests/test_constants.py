from src.constants import (
    CRITERIA_LIST,
    CRITERIA_LIST_RATINGS,
    METADATA_FIELDS,
    FIELDS_ITEM,
    ACCESS_STANDARD_VALUES,
    RESULT_TYPES,
    VERSION_COAR_LIST,
    FORMAT_DICT,
    BIBLIOGRAPHIC_MANAGERS,
    METADATA_EXPORT_TYPES,
    SOCIAL_NETWORKS,
    DOCUMENT_IDENTIFIER_LIST,
)


class TestConstants:
    def test_criteria_list_has_8_items(self):
        assert len(CRITERIA_LIST) == 8

    def test_criteria_list_matches_ratings_keys(self):
        assert set(CRITERIA_LIST) == set(CRITERIA_LIST_RATINGS.keys())

    def test_total_rating_sum(self):
        total = sum(CRITERIA_LIST_RATINGS.values())
        assert total == 67.5

    def test_metadata_fields_not_empty(self):
        assert len(METADATA_FIELDS) > 0
        assert "DC.creator" in METADATA_FIELDS

    def test_fields_item_not_empty(self):
        assert len(FIELDS_ITEM) > 0

    def test_access_standard_values(self):
        assert "openAccess" in ACCESS_STANDARD_VALUES
        assert "closedAccess" in ACCESS_STANDARD_VALUES

    def test_result_types_not_empty(self):
        assert len(RESULT_TYPES) > 0
        assert "article" in RESULT_TYPES

    def test_version_coar_list(self):
        assert "publishedVersion" in VERSION_COAR_LIST
        assert "draft" in VERSION_COAR_LIST

    def test_format_dict_structure(self):
        assert "text" in FORMAT_DICT
        assert "application" in FORMAT_DICT
        assert "pdf" in FORMAT_DICT["application"]

    def test_bibliographic_managers(self):
        assert "mendeley" in BIBLIOGRAPHIC_MANAGERS
        assert "zotero" in BIBLIOGRAPHIC_MANAGERS

    def test_metadata_export_types(self):
        assert "mets" in METADATA_EXPORT_TYPES
        assert "json" in METADATA_EXPORT_TYPES

    def test_social_networks(self):
        assert "facebook" in SOCIAL_NETWORKS
        assert "twitter" in SOCIAL_NETWORKS

    def test_document_identifier_list(self):
        assert "doi" in DOCUMENT_IDENTIFIER_LIST
        assert "handle" in DOCUMENT_IDENTIFIER_LIST
        assert "orcid" in DOCUMENT_IDENTIFIER_LIST
