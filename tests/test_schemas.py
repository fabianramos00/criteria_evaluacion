import pytest
from unittest.mock import patch
from src.api.schemas import (
    RegistrationSchema,
    VisibilitySchema,
    PolicySchema,
    LegalAspectsSchema,
    SecuritySchema,
    StatisticsSchema,
    ServicesSchema,
)


@pytest.mark.asyncio
async def test_registration_schema_valid():
    schema = RegistrationSchema(
        repository_url="https://example.com",
        repository_name="Test Repo",
    )
    assert "example.com" in str(schema.repository_url)
    assert schema.repository_names == ["Test Repo"]


@pytest.mark.asyncio
async def test_visibility_schema_no_urls_when_disabled():
    schema = VisibilitySchema(national_collector=False, initiatives_existence=True)
    assert schema.collector_urls is None


@pytest.mark.asyncio
async def test_visibility_schema_collects_urls():
    with patch("src.api.schemas.check_website", return_value=True):
        schema = VisibilitySchema(
            national_collector=True,
            initiatives_existence=True,
            collector_url1="https://example.com/url1",
            collector_url2="https://example.com/url2",
        )
    assert len(schema.collector_urls) == 2


@pytest.mark.asyncio
async def test_policy_schema():
    with patch("src.api.schemas.check_website", return_value=True):
        schema = PolicySchema(
            open_access=True,
            open_access_url="https://example.com/openaccess",
            metadata_reuse=False,
            content_preservation=False,
            deposit_data=False,
            action_policy=False,
            policy_data=False,
            vision_mission=False,
            contact=False,
            boai=False,
        )
    assert schema.open_access_url is not None


@pytest.mark.asyncio
async def test_legal_aspects_schema_conditional_url_required():
    with pytest.raises(ValueError):
        LegalAspectsSchema(
            author_property=True,
            author_permission=True,
            author_permission_url=None,
            editorial_policy=False,
            author_copyright=False,
        )


@pytest.mark.asyncio
async def test_security_schema_backups_url_required_when_enabled():
    with pytest.raises(ValueError):
        SecuritySchema(
            backups=True,
            backups_url=None,
            checksum=False,
            backups_location=False,
            format_control=False,
        )


@pytest.mark.asyncio
async def test_statistics_schema_requires_url_when_enabled():
    with pytest.raises(ValueError):
        StatisticsSchema(
            general_statistics=True,
            general_statistics_url=None,
            save_logs=False,
            counter=False,
        )


@pytest.mark.asyncio
async def test_services_schema():
    with patch("src.api.schemas.check_website", return_value=True):
        schema = ServicesSchema(
            rss_alert=True,
            author_profiles=True,
            author_profiles_url="https://example.com/profiles",
            cite_metrics=True,
            cite_metrics_url="https://example.com/metrics",
            new_metrics=False,
        )
    assert schema.author_profiles_url is not None
    assert schema.cite_metrics_url is not None


@pytest.mark.asyncio
async def test_conditional_required_field_missing():
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
