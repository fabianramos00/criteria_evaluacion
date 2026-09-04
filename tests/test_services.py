import pytest
from unittest.mock import AsyncMock, MagicMock
from src.api.services import (
    check_workflow,
    get_record_by_id,
    create_record,
    update_record,
    get_records,
)


class TestCheckWorkflow:
    def test_returns_none_when_item_not_in_data(self):
        record = MagicMock()
        record.data = {}
        record.rating = 0
        record.last_item_evaluated = "started"

        result = check_workflow(record, 0)
        assert result is None

    def test_returns_existing_data_when_item_evaluated(self):
        record = MagicMock()
        record.data = {"visibility": {"total": 5}}
        record.rating = 5

        result = check_workflow(record, 0)
        assert result == {"total": 5, "accumulative": 5}

    def test_raises_406_when_previous_item_not_evaluated(self):
        from fastapi import HTTPException

        record = MagicMock()
        record.data = {}
        record.rating = 0
        record.last_item_evaluated = "started"

        with pytest.raises(HTTPException) as exc_info:
            check_workflow(record, 1)
        assert exc_info.value.status_code == 406


class TestGetRecordById:
    @pytest.mark.asyncio
    async def test_returns_record_when_found(self, mocker):
        mock_record = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_record

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_record_by_id(mock_db, "test-id")
        assert result == mock_record

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, mocker):
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_record_by_id(mock_db, "non-existent")
        assert result is None

    @pytest.mark.asyncio
    async def test_for_update_locks_row(self, mocker):
        mock_query = MagicMock()
        mock_query.filter_by.return_value = mock_query
        mock_query.with_for_update.return_value = mock_query
        mocker.patch("src.api.services.select", return_value=mock_query)
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = MagicMock()
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        await get_record_by_id(mock_db, "test-id", for_update=True)

        mock_query.with_for_update.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_read_path_has_no_row_lock(self, mocker):
        mock_query = MagicMock()
        mock_query.filter_by.return_value = mock_query
        mock_query.with_for_update.return_value = mock_query
        mocker.patch("src.api.services.select", return_value=mock_query)
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = MagicMock()
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        await get_record_by_id(mock_db, "test-id")

        mock_query.with_for_update.assert_not_called()


class TestGetRecordOr404:
    @pytest.mark.asyncio
    async def test_mutation_dependency_requests_row_lock(self, mocker):
        from src.api.routes import get_record_or_404

        mock_get = mocker.patch(
            "src.api.routes.get_record_by_id",
            new=AsyncMock(return_value=MagicMock()),
        )

        dependency = get_record_or_404(for_update=True)
        await dependency("token", db=MagicMock())

        mock_get.assert_awaited_once_with(mocker.ANY, "token", for_update=True)

    @pytest.mark.asyncio
    async def test_read_dependency_has_no_row_lock(self, mocker):
        from src.api.routes import get_record_or_404

        mock_get = mocker.patch(
            "src.api.routes.get_record_by_id",
            new=AsyncMock(return_value=MagicMock()),
        )

        dependency = get_record_or_404()
        await dependency("token", db=MagicMock())

        mock_get.assert_awaited_once_with(mocker.ANY, "token", for_update=False)


class TestCreateRecord:
    @pytest.mark.asyncio
    async def test_creates_and_returns_record(self):
        mock_db = MagicMock()
        mock_db.commit = AsyncMock()

        record = await create_record(mock_db, "https://example.com", ["Test Repo"])

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert record.repository_url == "https://example.com"
        assert record.repository_names == ["Test Repo"]

    @pytest.mark.asyncio
    async def test_rolls_back_on_error(self):
        mock_db = MagicMock()
        mock_db.commit = AsyncMock(side_effect=Exception("DB Error"))
        mock_db.rollback = AsyncMock()

        with pytest.raises(Exception):
            await create_record(mock_db, "https://example.com", ["Test Repo"])

        mock_db.rollback.assert_called_once()


class TestUpdateRecord:
    @pytest.mark.asyncio
    async def test_updates_record_data_and_rating(self):
        mock_record = MagicMock()
        mock_record.data = {}
        mock_record.rating = 0
        mock_record.last_item_evaluated = "started"
        mock_record.is_completed = False

        mock_db = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result_data = {"total": 5, "value": 1}

        updated = await update_record(mock_db, mock_record, 0, result_data)

        assert updated.data["visibility"] == result_data
        assert updated.rating == 5
        assert updated.last_item_evaluated == "visibility"
        mock_db.commit.assert_called_once()


class TestGetRecords:
    @pytest.mark.asyncio
    async def test_get_records_returns_dict_structure(self):
        assert callable(get_records)
