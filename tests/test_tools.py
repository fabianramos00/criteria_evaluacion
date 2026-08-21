from unittest.mock import patch
from src.core.tools import check_website


def test_check_website_success():
    with patch("src.core.tools.get_sync_client") as mock_factory:
        mock_client = mock_factory.return_value
        mock_client.get.return_value.status_code = 200
        result = check_website("https://example.com")
        assert result is True


def test_check_website_redirect():
    with patch("src.core.tools.get_sync_client") as mock_factory:
        mock_client = mock_factory.return_value
        mock_client.get.return_value.status_code = 301
        result = check_website("https://example.com")
        assert result is True


def test_check_website_failure():
    with patch("src.core.tools.get_sync_client") as mock_factory:
        mock_client = mock_factory.return_value
        mock_client.get.return_value.status_code = 404
        result = check_website("https://example.com")
        assert result is False


def test_check_website_request_error():
    import httpx

    with patch("src.core.tools.get_sync_client") as mock_factory:
        mock_factory.return_value.get.side_effect = httpx.RequestError(
            "Connection error"
        )
        result = check_website("https://example.com")
        assert result is False
