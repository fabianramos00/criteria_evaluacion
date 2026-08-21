import pytest
from src.core.tools import get_schema_resume, is_similar
from src.core.policy import evaluate_policy
from src.core.security import evaluate_security
from src.core.services import evaluate_services, evaluate_items
from src.core.legal_aspects import evaluate_legal_aspects, check_author_rights
from src.api.schemas import (
    PolicySchema,
    SecuritySchema,
    ServicesSchema,
    LegalAspectsSchema,
)


class TestGetSchemaResume:
    def test_excludes_url_fields(self):
        schema = {
            "open_access": True,
            "open_access_url": "https://example.com",
        }
        result = get_schema_resume(schema)
        assert "open_access_url" not in result
        assert result["open_access"]["value"] == 1

    def test_includes_url_when_true(self):
        schema = {
            "open_access": True,
            "open_access_url": "https://example.com",
        }
        result = get_schema_resume(schema)
        assert result["open_access"]["value"] == 1
        assert result["open_access"]["url"] == "https://example.com"

    def test_includes_none_url_when_false(self):
        schema = {
            "open_access": False,
            "open_access_url": None,
        }
        result = get_schema_resume(schema)
        assert result["open_access"]["value"] == 0
        assert result["open_access"]["url"] is None


class TestIsSimilar:
    def test_similar_names(self):
        assert is_similar("Open Access Repository", "Open Access Repository") is True

    def test_different_names(self):
        assert (
            is_similar("completely different string xyz", "another random string abc")
            is False
        )

    def test_case_insensitive(self):
        assert is_similar("TEST REPO", "test repo") is True


class TestEvaluatePolicy:
    @pytest.mark.asyncio
    async def test_calculates_total(self):
        schema = PolicySchema(
            open_access=True,
            open_access_url="https://example.com/oa",
            metadata_reuse=False,
            content_preservation=False,
            deposit_data=False,
            action_policy=False,
            policy_data=False,
            vision_mission=False,
            contact=False,
            boai=False,
        )

        result = await evaluate_policy(["Test Repo"], schema)

        assert "total" in result
        assert isinstance(result["total"], (int, float))


class TestEvaluateSecurity:
    def test_calculates_total(self):
        schema = SecuritySchema(
            backups=True,
            backups_url="https://example.com/backups",
            checksum=False,
            backups_location=True,
            format_control=True,
        )

        result = evaluate_security(schema)

        assert "total" in result
        assert isinstance(result["total"], (int, float))
        assert result["backups"]["value"] == 1


class TestEvaluateServices:
    def test_evaluates_with_empty_links(self):
        schema = ServicesSchema(
            rss_alert=True,
            author_profiles=False,
            cite_metrics=False,
            new_metrics=False,
        )

        result = evaluate_services(schema, [])

        assert "total" in result
        assert result["rss_alert"] == 1

    def test_evaluates_items_with_links(self):
        schema = ServicesSchema(
            rss_alert=True,
            author_profiles=True,
            author_profiles_url="https://example.com/profiles",
            cite_metrics=False,
            new_metrics=False,
        )

        links = [
            {
                "url": "https://example.com/doc1",
                "bibliographic_managers": {"zotero": "link", "mendeley": "link"},
            }
        ]

        result = evaluate_services(schema, links)

        assert "total" in result
        assert "bibliographic_managers" in result


class TestEvaluateItems:
    def test_returns_zeros_for_empty_links(self):
        items = {"test_key": (["field1"], 2)}
        result = evaluate_items([], items)
        assert result == {"test_key": 0}

    def test_calculates_values_based_on_threshold(self):
        items = {"test": (["field1"], 1)}
        links = [{"test": {"field1": "value"}}]
        result = evaluate_items(links, items)
        assert result["test"] == 1


class TestCheckAuthorRights:
    def test_returns_zero_when_no_links(self):
        result = check_author_rights([])
        assert result["value"] == 0

    def test_returns_one_when_all_have_author_rights(self):
        links = [
            {"url": "https://example.com/1", "author_rights": True},
            {"url": "https://example.com/2", "author_rights": True},
        ]
        result = check_author_rights(links)
        assert result["value"] == 1

    def test_returns_zero_when_any_missing_author_rights(self):
        links = [
            {"url": "https://example.com/1", "author_rights": True},
            {"url": "https://example.com/2", "author_rights": False},
        ]
        result = check_author_rights(links)
        assert result["value"] == 0
        assert "https://example.com/2" in result["details"]


class TestEvaluateLegalAspects:
    def test_calculates_total_with_links(self):
        schema = LegalAspectsSchema(
            author_property=True,
            author_permission=True,
            author_permission_url="https://example.com/auth",
            editorial_policy=True,
            author_copyright=True,
        )

        links = [{"url": "https://example.com", "author_rights": True}]

        result = evaluate_legal_aspects(schema, links)

        assert "total" in result
        assert result["author_property"] == 1
