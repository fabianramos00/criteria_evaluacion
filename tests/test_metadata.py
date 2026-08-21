import pytest
from unittest.mock import AsyncMock
from bs4 import BeautifulSoup
from src.core.metadata import (
    check_metadata_date,
    check_access_name,
    check_types_research_result,
    check_format,
    check_version_format,
    check_language_format,
    check_author_id,
    search_items,
    validate_metadata,
    evaluate_metadata_group,
    limited_get_metadata,
    evaluate_metadata,
)
from src.api.schemas import MetadataSchema
from src.constants import (
    METADATA_FIELDS,
    ACCESS_STANDARD_VALUES,
)


class TestMetadataHelpers:
    def test_check_access_name_none(self):
        result = check_access_name(None)
        assert result is None

    def test_check_access_name_open_access(self):
        result = check_access_name(["closedAccess", "openAccess"])
        assert result in ACCESS_STANDARD_VALUES

    def test_check_access_name_closed_access(self):
        result = check_access_name(["restrictedAccess"])
        assert result == "restrictedAccess"

    def test_check_access_name_no_match(self):
        result = check_access_name(["unknownAccess"])
        assert result is None

    def test_check_types_research_result_empty(self):
        result = check_types_research_result(None)
        assert result is None

    def test_check_types_research_result_valid(self):
        result = check_types_research_result(["article", "book"])
        assert "article" in result

    def test_check_types_research_result_invalid(self):
        result = check_types_research_result(["unknown"])
        assert result is None

    def test_check_format_valid(self):
        result = check_format(["application/pdf"])
        assert result == "application/pdf"

    def test_check_format_invalid(self):
        result = check_format(["invalid/format"])
        assert result is None

    def test_check_format_empty(self):
        result = check_format(None)
        assert result is None

    def test_check_version_format_valid(self):
        result = check_version_format(["acceptedVersion", "draft"])
        assert "acceptedVersion" in result

    def test_check_version_format_invalid(self):
        result = check_version_format(["unknownVersion"])
        assert result is None

    def test_check_language_format_iso(self):
        result = check_language_format(["en", "part3"])
        assert result == "ISO 639-3"

    def test_check_language_format_zxx(self):
        result = check_language_format(["zxx"])
        assert result == "zxx"

    def test_check_language_format_none(self):
        result = check_language_format(None)
        assert result is None

    def test_check_author_id_single_orcid(self):
        result = check_author_id(["https://orcid.org/0000-0001"])
        assert result == "ORCID"

    def test_check_author_id_single_iralis(self):
        result = check_author_id(["https://www.iralis.org/123"])
        assert result == "IraLIS"

    def test_check_author_id_multiple_orcid_iralis(self):
        result = check_author_id(
            ["https://orcid.org/0000-0001", "https://www.iralis.org/123"]
        )
        assert result == "ORCID/IraLIS"

    def test_check_author_id_none(self):
        result = check_author_id(None)
        assert result is None


class TestSearchItems:
    def test_search_items_finds_in_href(self):
        html = BeautifulSoup(
            '<a href="/zotero"><img src="zotero.png" /></a>', "html.parser"
        )
        result = search_items(["zotero"], html)
        assert result["zotero"] == "/zotero"

    def test_search_items_finds_in_text(self):
        html = BeautifulSoup('<a href="/link">zotero</a>', "html.parser")
        result = search_items(["zotero"], html)
        assert result["zotero"] == "zotero"

    def test_search_items_finds_in_img_src(self):
        html = BeautifulSoup('<a><img src="/mendeley-logo.png" /></a>', "html.parser")
        result = search_items(["mendeley"], html)
        assert result["mendeley"] == "/mendeley-logo.png"

    def test_search_items_no_match(self):
        html = BeautifulSoup('<a href="/other">other</a>', "html.parser")
        result = search_items(["zotero"], html)
        assert result["zotero"] is None


class TestCheckMetadataDate:
    def test_check_metadata_date_valid_format(self):
        html = BeautifulSoup(
            '<html><head><meta name="DC.date" content="2024-01-15" /></head></html>',
            "html.parser",
        )
        date_dict, is_valid = check_metadata_date(html)
        assert is_valid is True
        assert date_dict is not None

    def test_check_metadata_date_invalid_format(self):
        html = BeautifulSoup(
            '<html><head><meta name="DC.date" content="invalid-date" /></head></html>',
            "html.parser",
        )
        date_dict, is_valid = check_metadata_date(html)
        assert is_valid is None or is_valid is False


class TestValidateMetadata:
    def test_validate_metadata_all_present(self):
        link_list = [
            {
                "url": "https://example.com",
                "metadata": {f: "value" for f in METADATA_FIELDS + ["DC.date"]},
            }
        ]
        fields_metadata, fields_dict = validate_metadata(link_list)
        assert all(v["value"] for v in fields_metadata.values())

    def test_validate_metadata_missing_field(self):
        link_list = [
            {
                "url": "https://example.com",
                "metadata": {"DC.creator": None},
            }
        ]
        fields_metadata, fields_dict = validate_metadata(link_list)
        assert fields_metadata["DC.creator"]["value"] is False


class TestEvaluateMetadataGroup:
    def test_evaluate_metadata_group_all_true(self):
        metadata_dict = {
            "field1": {"value": True},
            "field2": {"value": True},
        }
        result = evaluate_metadata_group(metadata_dict, ["field1", "field2"])
        assert result["value"] == 1

    def test_evaluate_metadata_group_some_false(self):
        metadata_dict = {
            "field1": {"value": True},
            "field2": {"value": False},
        }
        result = evaluate_metadata_group(metadata_dict, ["field1", "field2"])
        assert result["value"] == 0


class TestEvaluateMetadata:
    @pytest.mark.asyncio
    async def test_evaluate_metadata_with_empty_links(self, mocker):
        schema = MetadataSchema(
            curation=True,
            classification_system=True,
            metadata_schema=True,
            metadata_export=True,
        )

        mocker.patch("src.core.metadata.limited_get_metadata", new_callable=AsyncMock)

        result, links = await evaluate_metadata(schema, [])
        assert "total" in result
        assert result["curation"] == 1


class TestLimitedGetMetadata:
    @pytest.mark.asyncio
    async def test_limited_get_metadata_returns_result(self, mocker):
        link_dict = {"url": "https://example.com"}

        mocker.patch(
            "src.core.metadata.get_metadata",
            new_callable=AsyncMock,
            return_value=link_dict,
        )

        result = await limited_get_metadata(link_dict)
        assert result == link_dict
