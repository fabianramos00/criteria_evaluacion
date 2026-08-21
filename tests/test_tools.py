from unittest.mock import patch
from src.core.tools import check_website


def test_check_website_success():
    with patch("httpx.get") as mock_get:
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        result = check_website("https://example.com")
        assert result is True


def test_check_website_redirect():
    with patch("httpx.get") as mock_get:
        mock_response = mock_get.return_value
        mock_response.status_code = 301
        result = check_website("https://example.com")
        assert result is True


def test_check_website_failure():
    with patch("httpx.get") as mock_get:
        mock_response = mock_get.return_value
        mock_response.status_code = 404
        result = check_website("https://example.com")
        assert result is False


def test_check_website_request_error():
    import httpx

    with patch("httpx.get", side_effect=httpx.RequestError("Connection error")):
        result = check_website("https://example.com")
        assert result is False
