from src.core.tools import get_schema_resume
from src.api.schemas import SecuritySchema


def evaluate_security(security_schema: SecuritySchema) -> dict:
    security_resume = get_schema_resume(security_schema.dict())
    security_resume["total"] = sum(
        v["value"] if isinstance(v, dict) else v for v in security_resume.values()
    )
    return security_resume
