import json

import pytest
import httpx
from unittest.mock import AsyncMock, patch

from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from starlette.requests import Request

from src.api.schemas import (
    RegistrationSchema,
    VisibilitySchema,
    PolicySchema,
    LegalAspectsSchema,
    SecuritySchema,
    StatisticsSchema,
    ServicesSchema,
)
from src.core.tools import check_website_async


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
    schema = VisibilitySchema(
        national_collector=True,
        initiatives_existence=True,
        collector_url1="https://example.com/url1",
        collector_url2="https://example.com/url2",
    )
    assert len(schema.collector_urls) == 2


@pytest.mark.asyncio
async def test_policy_schema():
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


def _policy_schema_with_url() -> PolicySchema:
    return PolicySchema(
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


@pytest.mark.asyncio
async def test_check_website_async_success_codes():
    for code in (200, 301, 302):
        with patch("src.core.tools.get_async_client") as mock_factory:
            mock_factory.return_value.get = AsyncMock(
                return_value=type("R", (), {"status_code": code})()
            )
            assert await check_website_async("https://example.com") is True


@pytest.mark.asyncio
async def test_check_website_async_error():
    with patch("src.core.tools.get_async_client") as mock_factory:
        mock_factory.return_value.get = AsyncMock(
            side_effect=httpx.RequestError("Connection error")
        )
        assert await check_website_async("https://example.com") is False


@pytest.mark.asyncio
async def test_validate_async_raises_on_unreachable_url():
    with patch("src.api.schemas.check_website_async", return_value=False):
        with pytest.raises(RequestValidationError) as exc_info:
            await _policy_schema_with_url().validate_async()
    errors = exc_info.value.errors()
    assert errors[0]["loc"] == ("body", "open_access_url")
    assert errors[0]["msg"] == "URL no accesible"


@pytest.mark.asyncio
async def test_validate_async_passes_when_reachable():
    with patch("src.api.schemas.check_website_async", return_value=True):
        await _policy_schema_with_url().validate_async()


@pytest.mark.asyncio
async def test_validate_async_skips_none_urls():
    with patch("src.api.schemas.check_website_async", return_value=False) as mock_check:
        schema = VisibilitySchema(national_collector=False, initiatives_existence=True)
        await schema.validate_async()
    mock_check.assert_not_called()


@pytest.mark.asyncio
async def test_validate_async_checks_collector_urls():
    with patch("src.api.schemas.check_website_async", return_value=False):
        with pytest.raises(RequestValidationError) as exc_info:
            await VisibilitySchema(
                national_collector=True,
                initiatives_existence=True,
                collector_url1="https://example.com/url1",
            ).validate_async()
    assert exc_info.value.errors()[0]["loc"] == ("body", "collector_url1")

    with patch("src.api.schemas.check_website_async", return_value=True):
        await VisibilitySchema(
            national_collector=True,
            initiatives_existence=True,
            collector_url1="https://example.com/url1",
        ).validate_async()


@pytest.mark.asyncio
async def test_request_validation_error_wire_format_422():
    with patch("src.api.schemas.check_website_async", return_value=False):
        with pytest.raises(RequestValidationError) as exc_info:
            await _policy_schema_with_url().validate_async()

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/policy/{token}",
            "headers": [],
            "query_string": b"",
            "server": ("test", 80),
            "scheme": "http",
        }
    )
    response = await request_validation_exception_handler(request, exc_info.value)
    assert response.status_code == 422
    detail = json.loads(response.body)["detail"]
    assert detail[0]["loc"] == ["body", "open_access_url"]
    assert detail[0]["msg"] == "URL no accesible"
