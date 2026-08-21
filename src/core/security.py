from src.core.tools import get_schema_resume, sum_resume
from src.api.schemas import SecuritySchema


def evaluate_security(security_schema: SecuritySchema) -> dict:
    security_resume = get_schema_resume(security_schema.model_dump())
    security_resume["total"] = sum_resume(security_resume)
    return security_resume
