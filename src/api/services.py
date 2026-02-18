from fastapi import HTTPException
from sqlalchemy import select, func, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from src.database.models import Record
from src.api.schemas import RecordOut
from src.constants import CRITERIA_LIST


async def get_record_by_id(db: AsyncSession, id: str):
    try:
        result = await db.execute(select(Record).filter_by(id=id))
        return result.scalars().first()
    except Exception as e:
        print(f"Error getting record: {e}")
        return None


async def get_records(
    db: AsyncSession, page: int, limit: int, search: str | None = None
) -> dict:
    offset = (page - 1) * limit
    query = select(Record).order_by(Record.updated_at.desc())
    if search:
        query = query.where(
            or_(
                Record.repository_url.ilike(f"%{search}%"),
                cast(Record.repository_names, String).ilike(f"%{search}%"),
            )
        )

    result = await db.execute(query.offset(offset).limit(limit))
    records = result.scalars().all()
    count_query = select(func.count(Record.id))
    if search:
        count_query = count_query.where(
            or_(
                Record.repository_url.ilike(f"%{search}%"),
                cast(Record.repository_names, String).ilike(f"%{search}%"),
            )
        )

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


def check_workflow(record: Record, item_index: int):
    data = record.data
    item = CRITERIA_LIST[item_index]
    if item in data:
        item_data = data[item]
        item_data["accumulative"] = record.rating
        return item_data

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
    except Exception as e:
        await db.rollback()
        raise e


async def update_record(
    db: AsyncSession,
    record: Record,
    item_index: int,
    result: dict,
    links: list[dict] | None = None,
) -> Record:
    item = CRITERIA_LIST[item_index]
    record.data = {**record.data, item: result}
    record.rating += result["total"]
    if links is not None:
        record.links = links
        flag_modified(record, "links")
    record.last_item_evaluated = item
    record.is_completed = item_index == len(CRITERIA_LIST) - 1
    db.add(record)
    await db.commit()
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
