from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import get_db
from src.database.models import Record
from src.api.services import create_record, get_record_by_id, update_record_and_format_response, get_records
from src.api.schemas import (
    RegistrationSchema, VisibilitySchema, PolicySchema, LegalAspectsSchema, 
    MetadataSchema, InteroperabilitySchema, SecuritySchema, StatisticsSchema, 
    ServicesSchema, RecordOut
)
from src.core.visibility import evaluate_visibility
from src.core.policy import evaluate_policy
from src.core.legal_aspects import evaluate_legal_aspects
from src.core.metadata import evaluate_metadata
from src.core.interoperability import evaluate_interoperability
from src.core.security import evaluate_security
from src.core.statistics import evaluate_statistics
from src.core.services import evaluate_services
from src.constants import CRITERIA_LIST

router = APIRouter()


async def get_record_or_404(token: str, db: AsyncSession = Depends(get_db)) -> Record:
    if not token:
        raise HTTPException(status_code=400, detail="Token required")
    record = await get_record_by_id(db, token)
    if not record:
        raise HTTPException(status_code=404, detail="Invalid token")
    return record


def check_workflow(record: Record, item_index: int):
    data = record.data
    item = CRITERIA_LIST[item_index]
    if item in data:
        item_data = data[item]
        item_data['accumulative'] = record.rating
        return item_data
    
    if item_index != 0:
        try:
            prev_item_index = item_index - 1
            if prev_item_index >= 0 and CRITERIA_LIST[prev_item_index] != record.last_item_evaluated:
                raise HTTPException(status_code=406, detail='Last item not evaluated')
        except ValueError:
            pass
    return None

@router.post("/")
async def home(registration: RegistrationSchema, db: AsyncSession = Depends(get_db)):
    record = await create_record(
        db, 
        str(registration.repository_url), 
        registration.repository_names
    )
    return {'token': record.id}


@router.post("/visibility/{token}")
async def visibility(
    token: str,
    visibility_schema: VisibilitySchema,
    db: AsyncSession = Depends(get_db),
    record: Record = Depends(get_record_or_404)
):
    existing_result = check_workflow(record, 0)
    if existing_result:
        return existing_result  
    result, links_dict = await evaluate_visibility(db, record, visibility_schema)
    return await update_record_and_format_response(db, record, 0, result, links_dict)


@router.post("/policy/{token}")
async def policy(
    token: str,
    policy_schema: PolicySchema,
    db: AsyncSession = Depends(get_db),
    record: Record = Depends(get_record_or_404)
):
    existing_result = check_workflow(record, 1)
    if existing_result:
        return existing_result
    result = await evaluate_policy(record.repository_names, policy_schema)
    return await update_record_and_format_response(db, record, 1, result)


@router.post("/legal_aspects/{token}")
async def legal_aspects(
    token: str,
    legal_aspects_schema: LegalAspectsSchema,
    db: AsyncSession = Depends(get_db),
    record: Record = Depends(get_record_or_404)
):
    existing_result = check_workflow(record, 2)
    if existing_result:
        return existing_result
    result = evaluate_legal_aspects(legal_aspects_schema, record.links)
    return await update_record_and_format_response(db, record, 2, result)


@router.post("/metadata/{token}")
async def metadata(
    token: str,
    metadata_schema: MetadataSchema,
    db: AsyncSession = Depends(get_db),
    record: Record = Depends(get_record_or_404)
):
    existing_result = check_workflow(record, 3)
    if existing_result:
        return existing_result
    result, links = await evaluate_metadata(metadata_schema, record.metadata)
    return await update_record_and_format_response(db, record, 3, result, links)


@router.post("/interoperability/{token}")
async def interoperability(
    token: str,
    interoperability_schema: InteroperabilitySchema,
    db: AsyncSession = Depends(get_db),
    record: Record = Depends(get_record_or_404)
):
    existing_result = check_workflow(record, 4)
    if existing_result:
        return existing_result
    result = evaluate_interoperability(interoperability_schema, record)
    return await update_record_and_format_response(db, record, 4, result)


@router.post("/security/{token}")
async def security(
    token: str,
    security_schema: SecuritySchema,
    db: AsyncSession = Depends(get_db),
    record: Record = Depends(get_record_or_404)
):
    existing_result = check_workflow(record, 5)
    if existing_result:
        return existing_result
    result = evaluate_security(security_schema)
    return await update_record_and_format_response(db, record, 5, result)



@router.post("/statistics/{token}")
async def statistics(
    token: str,
    statistics_schema: StatisticsSchema,
    db: AsyncSession = Depends(get_db),
    record: Record = Depends(get_record_or_404)
):
    existing_result = check_workflow(record, 6)
    if existing_result:
        return existing_result    
    result, links_dict = await evaluate_statistics(statistics_schema, record.links)
    return await update_record_and_format_response(db, record, 6, result, links_dict)


@router.post("/services/{token}")
async def services(
    token: str,
    services_schema: ServicesSchema,
    db: AsyncSession = Depends(get_db),
    record: Record = Depends(get_record_or_404)
):
    existing_result = check_workflow(record, 7)
    if existing_result:
        return existing_result
    result = evaluate_services(services_schema, record.links)
    return await update_record_and_format_response(db, record, 7, result)



@router.get("/{item}/{token}")
async def get_data(
    item: str,
    token: str,
    db: AsyncSession = Depends(get_db),
    record: Record = Depends(get_record_or_404)
):
    if item not in CRITERIA_LIST:
        raise HTTPException(status_code=400, detail="Invalid item")
    is_next = False
    if not record.is_completed:
        if record.last_item_evaluated == 'started' and item == CRITERIA_LIST[0]:
            is_next = True
        elif record.last_item_evaluated in CRITERIA_LIST:
            last_idx = CRITERIA_LIST.index(record.last_item_evaluated)
            if last_idx + 1 < len(CRITERIA_LIST) and item == CRITERIA_LIST[last_idx + 1]:
                is_next = True
    if item not in record.data:
        return JSONResponse(status_code=404, content={'is_next': is_next, 'is_completed': False})
    item_data = record.data[item]
    item_data.update({
        'accumulative': record.rating,
        'is_next': is_next,
        'is_completed': True
    })

    return item_data


@router.get("/list")
async def get_list(
    page: int = 1,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    return await get_records(db, page, limit)


@router.get("/summary/{token}")
async def get_summary(
    token: str,
    record: Record = Depends(get_record_or_404)
):
    record_dict = RecordOut.model_validate(record).model_dump()
    summary_list = []
    for i in CRITERIA_LIST:
        item_data = record.data.get(i, {})
        summary_list.append({
            'item': i, 
            'total': item_data.get('total', 0), 
        })
    record_dict['summary'] = summary_list
    return record_dict