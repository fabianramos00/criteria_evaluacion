import pytest
from unittest.mock import MagicMock, AsyncMock
from src.core.visibility import (
    standard_name,
    friendly_secure_url,
    count_items,
    count_national_collectors,
    search_in,
    is_open_access,
    open_access,
    execute_async_search,
)
from src.core.statistics import (
    statistics_url_exists,
    evaluate_urls_statistics,
)
from src.core.interoperability import (
    check_collectors,
    check_oai_pmh,
    check_identifier,
    evaluate_interoperability,
)
from src.api.schemas import InteroperabilitySchema


class TestVisibilityHelpers:
    def test_standard_name_empty_data(self):
        result = standard_name({})
        assert result["value"] == 1.5

    def test_standard_name_all_same_names(self):
        data = {"a": {"name": "Repo"}, "b": {"name": "Repo"}}
        result = standard_name(data)
        assert result["value"] == 1.5

    def test_standard_name_different_names(self):
        data = {"a": {"name": "Repo A"}, "b": {"name": "Repo B"}}
        result = standard_name(data)
        assert result["value"] == 0

    def test_friendly_secure_url_https_short(self):
        result = friendly_secure_url("https://repo.example.com")
        assert result["value"] == 1.5
        assert "Friendly" in result["text"]

    def test_friendly_secure_url_no_https(self):
        result = friendly_secure_url("http://repo.example.com")
        assert result["value"] == 0
        assert "Insecure" in result["text"]

    def test_friendly_secure_url_too_long(self):
        long_url = "https://" + "a" * 41 + ".com"
        result = friendly_secure_url(long_url)
        assert result["value"] == 0
        assert "Not a friendly URL" in result["text"]

    def test_count_items_none(self):
        result = count_items({}, "test")
        assert result["value"] == 0

    def test_count_items_all(self):
        data = {"a": "value1", "b": "value2"}
        result = count_items(data, "test")
        assert result["value"] == 1.5

    def test_count_items_some(self):
        data = {"a": "value1", "b": None}
        result = count_items(data, "test")
        assert result["value"] == 1

    def test_count_national_collectors_none(self):
        result = count_national_collectors(None)
        assert result["value"] == 0

    def test_count_national_collectors_five(self):
        result = count_national_collectors(["a", "b", "c", "d", "e"])
        assert result["value"] == 1.5

    def test_count_national_collectors_some(self):
        result = count_national_collectors(["a", "b"])
        assert result["value"] == 1


class TestVisibilityAsync:
    @pytest.mark.asyncio
    async def test_search_in_returns_first_match(self):
        async def mock_func(name):
            if name == "second":
                return {"found": name}
            return None

        result = await search_in(mock_func, ["first", "second", "third"])
        assert result == {"found": "second"}

    @pytest.mark.asyncio
    async def test_search_in_returns_none_when_no_match(self):
        async def mock_func(name):
            return None

        result = await search_in(mock_func, ["first", "second"])
        assert result is None

    @pytest.mark.asyncio
    async def test_is_open_access_success(self, mocker):
        mock_page = mocker.Mock()
        mock_page.content = b"""
            <html><head><meta name="DC.rights" content="openAccess" /></head></html>
        """

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_page

        mocker.patch("src.core.visibility.get_async_client", return_value=mock_client)

        result = await is_open_access("https://example.com")

        assert result["open_access"] is True
        assert result["author_rights"] is True

    @pytest.mark.asyncio
    async def test_is_open_access_request_error(self, mocker):
        import httpx

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.RequestError("error")

        mocker.patch("src.core.visibility.get_async_client", return_value=mock_client)

        result = await is_open_access("https://example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_open_access_all_open(self, mocker):
        visibility_dict = {
            "repo1": {"links": ["https://example.com/1", "https://example.com/2"]},
            "repo2": {"links": ["https://example.com/3"]},
        }

        mocker.patch(
            "src.core.visibility.is_open_access",
            new_callable=AsyncMock,
            side_effect=[
                {
                    "url": "https://example.com/1",
                    "open_access": True,
                    "author_rights": True,
                },
                {
                    "url": "https://example.com/2",
                    "open_access": True,
                    "author_rights": True,
                },
                {
                    "url": "https://example.com/3",
                    "open_access": True,
                    "author_rights": True,
                },
            ],
        )

        result, dict_list = await open_access(visibility_dict)
        assert result["value"] == 1

    @pytest.mark.asyncio
    async def test_open_access_with_none_result(self, mocker):
        visibility_dict = {
            "repo1": {"links": ["https://example.com/1", "https://example.com/2"]},
        }

        mocker.patch(
            "src.core.visibility.is_open_access",
            new_callable=AsyncMock,
            side_effect=[
                {
                    "url": "https://example.com/1",
                    "open_access": True,
                    "author_rights": True,
                },
                None,
            ],
        )

        result, dict_list = await open_access(visibility_dict)
        assert result["value"] == 0
        assert None not in dict_list

    @pytest.mark.asyncio
    async def test_execute_async_search(self):
        async def mock_search(name):
            return f"result_for_{name}"

        func_dict = {
            "source1": lambda n: mock_search(n),
            "source2": lambda n: mock_search(n),
        }

        tasks = {k: v for k, v in func_dict.items()}
        results = await execute_async_search(tasks, ["test_repo"])
        assert isinstance(results, dict)


class TestStatisticsAsync:
    @pytest.mark.asyncio
    async def test_statistics_url_exist_success(self, mocker):
        mock_response = mocker.Mock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        mocker.patch("src.core.statistics.get_async_client", return_value=mock_client)

        result = await statistics_url_exists("https://example.com")

        assert result == "https://example.com/statistics"

    @pytest.mark.asyncio
    async def test_statistics_url_exist_not_found(self, mocker):
        mock_response = mocker.Mock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        mocker.patch("src.core.statistics.get_async_client", return_value=mock_client)

        result = await statistics_url_exists("https://example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_statistics_url_exist_connection_error(self, mocker):
        import httpx

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")

        mocker.patch("src.core.statistics.get_async_client", return_value=mock_client)

        result = await statistics_url_exists("https://example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_evaluate_urls_statistics_empty(self):
        result = await evaluate_urls_statistics([])
        assert result["value"] == 0

    @pytest.mark.asyncio
    async def test_evaluate_urls_statistics_all_have_stats(self, mocker):
        link_list = [
            {"url": "https://example.com/1"},
            {"url": "https://example.com/2"},
        ]

        mocker.patch(
            "src.core.statistics.limited_statistics_url_exist",
            new_callable=AsyncMock,
            side_effect=[
                "https://example.com/1/statistics",
                "https://example.com/2/statistics",
            ],
        )

        result = await evaluate_urls_statistics(link_list)
        assert result["value"] == 1

    @pytest.mark.asyncio
    async def test_evaluate_urls_statistics_some_missing(self, mocker):
        link_list = [
            {"url": "https://example.com/1"},
            {"url": "https://example.com/2"},
        ]

        mocker.patch(
            "src.core.statistics.limited_statistics_url_exist",
            new_callable=AsyncMock,
            side_effect=["https://example.com/1/statistics", None],
        )

        result = await evaluate_urls_statistics(link_list)
        assert result["value"] == 0
        assert "https://example.com/2" in result["details"]


class TestInteroperability:
    def test_check_collectors_both_present(self):
        data = {"LA-Referencia": {"name": "LA"}, "OpenAIRE": {"name": "OA"}}
        result = check_collectors(data)
        assert result["value"] == 1

    def test_check_collectors_neither_present(self):
        data = {}
        result = check_collectors(data)
        assert result["value"] == 0

    def test_check_collectors_only_la(self):
        data = {"LA-Referencia": {"name": "LA"}}
        result = check_collectors(data)
        assert result["value"] == 0
        assert "Not present in OpenAIRE" in result["text"]

    def test_check_collectors_only_openaire(self):
        data = {"OpenAIRE": {"name": "OA"}}
        result = check_collectors(data)
        assert result["value"] == 0
        assert "Not present in LA Referencia" in result["text"]

    def test_check_oai_pmh_present(self):
        result = check_oai_pmh({"host": "https://example.com"})
        assert result["value"] == 1

    def test_check_oai_pmh_none(self):
        result = check_oai_pmh(None)
        assert result["value"] == 0

    def test_check_identifier_empty_links(self):
        result = check_identifier([])
        assert result["value"] == 0

    def test_check_identifier_valid_doi(self):
        links = [{"metadata": {"DC.identifier": "https://doi.org/10.1234/test"}}]
        result = check_identifier(links)
        assert result["value"] == 1

    def test_check_identifier_invalid(self):
        links = [
            {"metadata": {"DC.identifier": "invalid"}, "url": "https://example.com"}
        ]
        result = check_identifier(links)
        assert result["value"] == 0
        assert "https://example.com" in result["details"]

    def test_evaluate_interoperability(self):
        mock_record = MagicMock()
        mock_record.data = {
            "visibility": {
                "collector": {"details": {"LA-Referencia": {}, "OpenAIRE": {}}}
            },
            "metadata": {"dublin_core": True},
        }
        mock_record.data["visibility"]["directory"] = {
            "details": {"OAI-PMH": {"host": "https://example.com"}}
        }
        mock_record.links = []

        schema = InteroperabilitySchema(
            deleted_records=True,
            life_time=True,
            admin_email=True,
            identify_description=True,
            progressive_delivery=True,
            records_size=True,
            records_datestamp=True,
            systems_integration=True,
            share_data=True,
        )

        result = evaluate_interoperability(schema, mock_record)
        assert "total" in result
        assert "collector" in result
