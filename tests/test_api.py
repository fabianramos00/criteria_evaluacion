import json

import pytest
from fastapi.testclient import TestClient
from src.main import create_app


class TestHealthEndpoint:
    def test_root_returns_405_for_get(self):
        app = create_app()
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 405

    def test_root_accepts_post(self):
        app = create_app()
        client = TestClient(app)
        response = client.post("/", json={})
        assert response.status_code != 500


class TestVisibilitySchemaValidation:
    def test_visibility_requires_national_collector_url_when_true(self):
        from src.api.schemas import VisibilitySchema

        with pytest.raises(ValueError):
            VisibilitySchema(
                national_collector=True,
                initiatives_existence=True,
                collector_url1=None,
            )


class TestPolicySchemaValidation:
    def test_policy_requires_open_access_url_when_true(self):
        from src.api.schemas import PolicySchema

        with pytest.raises(ValueError):
            PolicySchema(
                open_access=True,
                open_access_url=None,
                metadata_reuse=False,
                content_preservation=False,
                deposit_data=False,
                action_policy=False,
                policy_data=False,
                vision_mission=False,
                contact=False,
                boai=False,
            )


class TestSecuritySchemaValidation:
    def test_security_requires_backups_url_when_true(self):
        from src.api.schemas import SecuritySchema

        with pytest.raises(ValueError):
            SecuritySchema(
                backups=True,
                backups_url=None,
                checksum=False,
                backups_location=False,
                format_control=False,
            )


class TestLegalAspectsSchemaValidation:
    def test_legal_aspects_requires_permission_url_when_true(self):
        from src.api.schemas import LegalAspectsSchema

        with pytest.raises(ValueError):
            LegalAspectsSchema(
                author_property=True,
                author_permission=True,
                author_permission_url=None,
                editorial_policy=False,
                author_copyright=False,
            )


class TestStatisticsSchemaValidation:
    def test_statistics_requires_url_when_enabled(self):
        from src.api.schemas import StatisticsSchema

        with pytest.raises(ValueError):
            StatisticsSchema(
                general_statistics=True,
                general_statistics_url=None,
                save_logs=False,
                counter=False,
            )


class TestServicesSchemaValidation:
    def test_services_requires_profiles_url_when_true(self):
        from src.api.schemas import ServicesSchema

        with pytest.raises(ValueError):
            ServicesSchema(
                rss_alert=True,
                author_profiles=True,
                author_profiles_url=None,
                cite_metrics=False,
                new_metrics=False,
            )


class TestFreshRecordDetailSummary:
    def _fresh_record(self):
        from types import SimpleNamespace

        return SimpleNamespace(
            last_item_evaluated="started",
            is_completed=False,
            data={},
            rating=0.0,
        )

    def test_last_criterion_index_started_returns_minus_one(self):
        from src.api.routes import last_criterion_index

        assert last_criterion_index(self._fresh_record()) == -1

    def test_next_item_for_started_returns_visibility(self):
        from src.api.routes import next_item_for

        assert next_item_for(self._fresh_record()) == "visibility"

    @pytest.mark.asyncio
    async def test_get_data_does_not_raise_for_started(self):
        from src.api.routes import get_data

        response = await get_data(
            item="visibility",
            token="test-token",
            db=None,
            record=self._fresh_record(),
        )
        assert response.status_code == 404
        body = json.loads(response.body)
        assert body["next_item"] == "visibility"
        assert body["is_next"] is True

    @pytest.mark.asyncio
    async def test_get_summary_does_not_raise_for_started(self):
        from src.api.routes import get_summary

        response = await get_summary(
            token="test-token",
            record=self._fresh_record(),
        )
        assert response.status_code == 400
        body = json.loads(response.body)
        assert body["next_item"] == "visibility"
