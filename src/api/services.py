import logging
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select, func, or_, cast, ARRAY, Text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Record
from src.api.schemas import RecordOut
from src.constants import CRITERIA_LIST

logger = logging.getLogger(__name__)


async def get_record_by_id(
    db: AsyncSession, record_id: str, for_update: bool = False
) -> Record | None:
    try:
        query = select(Record).filter_by(id=record_id)
        if for_update:
            query = query.with_for_update()
        result = await db.execute(query)
        return result.scalars().first()
    except Exception:
        logger.exception("Error getting record %s", record_id)
        raise


async def get_records(
    db: AsyncSession, page: int, limit: int, search: str | None = None
) -> dict:
    offset = (page - 1) * limit
    search_filter = None
    if search:
        search_filter = or_(
            Record.repository_url.ilike(f"%{search}%"),
            func.repository_names_text(
                cast(Record.repository_names, ARRAY(Text))
            ).ilike(f"%{search}%"),
        )
    query = select(Record).order_by(Record.updated_at.desc())
    if search_filter is not None:
        query = query.where(search_filter)

    result = await db.execute(query.offset(offset).limit(limit))
    records = result.scalars().all()
    count_query = select(func.count(Record.id))
    if search_filter is not None:
        count_query = count_query.where(search_filter)

    total_result = await db.execute(count_query)
    total_records = total_result.scalar_one()
    pages = (total_records + limit - 1) // limit
    has_next = page < pages
    has_prev = page > 1
    return {
        "has_prev": has_prev,
        "has_next": has_next,
        "prev_num": page - 1 if has_prev else None,
        "next_num": page + 1 if has_next else None,
        "pages": pages,
        "total_records": total_records,
        "items": [RecordOut.model_validate(r).model_dump() for r in records],
    }


def check_workflow(record: Record, item_index: int) -> dict | None:
    data = record.data
    item = CRITERIA_LIST[item_index]
    if item in data:
        return {**data[item], "accumulative": record.rating}

    if item_index != 0:
        try:
            prev_item_index = item_index - 1
            if (
                prev_item_index >= 0
                and CRITERIA_LIST[prev_item_index] != record.last_item_evaluated
            ):
                raise HTTPException(status_code=406, detail="Last item not evaluated")
        except ValueError:
            pass
    return None


async def create_record(
    db: AsyncSession, repository_url: str, repository_names: list[str]
) -> Record:
    try:
        record = Record(
            **{
                "repository_url": str(repository_url),
                "repository_names": repository_names,
            }
        )
        db.add(record)
        await db.commit()
        return record
    except Exception:
        await db.rollback()
        raise


async def update_record(
    db: AsyncSession,
    record: Record,
    item_index: int,
    result: dict,
    links: list[dict] | None = None,
) -> Record:
    item = CRITERIA_LIST[item_index]
    record.data = {**record.data, item: result}
    record.rating = (record.rating or 0) + Decimal(str(result["total"]))
    if links is not None:
        record.links = links
    record.last_item_evaluated = item
    record.is_completed = item_index == len(CRITERIA_LIST) - 1
    db.add(record)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(record)
    return record


async def update_record_and_format_response(
    db: AsyncSession,
    record: Record,
    item_index: int,
    result: dict,
    links: list[dict] | None = None,
) -> dict:
    record_updated = await update_record(db, record, item_index, result, links)
    result["accumulative"] = record_updated.rating
    return result
