from src.database.models import Record
from src.constants import DOCUMENT_IDENTIFIER_LIST
from src.core.tools import get_schema_resume
from src.api.schemas import InteroperabilitySchema


def check_collectors(data: dict):
    la, openaire = data.get("LA-Referencia"), data.get("OpenAIRE")
    if la and openaire:
        return {"value": 1, "text": "Presence in both collectors"}
    if not la and not openaire:
        return {"value": 0, "text": "Not present in both collectors"}
    if not la:
        return {"value": 0, "text": "Not present in LA Referencia"}
    return {"value": 0, "text": "Not present in OpenAIRE"}


def check_oai_pmh(oai_pmh_value: dict | None) -> dict:
    if oai_pmh_value is not None:
        return {"value": 1, "url": oai_pmh_value["host"]}
    return {"value": 0, "url": None}


def check_identifier(links: list[dict]) -> dict:
    result = {"value": 1, "details": []}
    if not links:
        result["value"] = 0
        return result
    for item in links:
        identifier = item["metadata"].get("DC.identifier", "")
        if not any(ext in identifier for ext in DOCUMENT_IDENTIFIER_LIST):
            result["value"] = 0
            result["details"].append(item["url"])

    return result


def evaluate_interoperability(
    interoperability_schema: InteroperabilitySchema, record: Record
) -> dict:
    data = record.data
    interoperability_resume = get_schema_resume(interoperability_schema.dict())
    interoperability_resume["collector"] = check_collectors(
        data["visibility"]["collector"]["details"]
    )
    interoperability_resume["oai_pmh"] = check_oai_pmh(
        data["visibility"]["directory"]["details"]["OAI-PMH"]
    )
    interoperability_resume["headers_html"] = data["metadata"]["dublin_core"]
    interoperability_resume["standard_identifier"] = check_identifier(record.links)
    interoperability_resume["total"] = sum(
        v["value"] if isinstance(v, dict) else v
        for v in interoperability_resume.values()
    )
    return interoperability_resume
