from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Record
from src.api.schemas import RecordOut
from src.constants import CRITERIA_LIST


async def get_record_by_id(db: AsyncSession, id: str):
    result = await db.execute(select(Record).filter_by(id=id))
    return result.scalars().first()


async def get_records(db: AsyncSession, page: int, limit: int) -> dict:
    offset = (page - 1) * limit
    result = await db.execute(
        select(Record)
        .order_by(Record.last_updated.desc())
        .offset(offset)
        .limit(limit)
    )
    records = result.scalars().all()
    total_result = await db.execute(select(func.count(Record.id)))
    total_records = total_result.scalar_one()
    pages = (total_records + limit - 1) // limit
    has_next = page < pages
    has_prev = page > 1
    return {
        'has_prev': has_prev,
        'has_next': has_next,
        'prev_num': page - 1 if has_prev else None,
        'next_num': page + 1 if has_next else None,
        'pages': pages,
        'total_records': total_records,
        'items': [RecordOut.model_validate(r).model_dump() for r in records]
    }


async def create_record(
    db: AsyncSession, 
    repository_url: str, 
    repository_names: list[str]
) -> Record:
    record = Record(**{
        'repository_url': str(repository_url),
        'repository_names': repository_names
    })
    db.add(record)
    await db.commit()
    return record


async def update_record(
    db: AsyncSession,
    record: Record,
    item_index: int,
    result: dict,
    links: list[dict] | None = None
) -> Record:
    item = CRITERIA_LIST[item_index]
    record.data.update({item: result})
    record.rating += result['total']
    if links is not None:
        record.links = links
    record.last_item_evaluated = item
    record.is_completed = item_index == len(CRITERIA_LIST) - 1
    db.add(record)
    await db.commit()
    return record


async def update_record_and_format_response(
    db: AsyncSession, 
    record: Record, 
    item_index: int,
    result: dict, 
    links: list[dict] | None = None
) -> dict:
    record_updated = await update_record(db, record, item_index, result, links)
    result['accumulative'] = record_updated.rating
    return result