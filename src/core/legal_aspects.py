from src.api.schemas import LegalAspectsSchema
from src.core.tools import get_schema_resume


def check_author_rights(link_list: list[dict]) -> dict:
    if not link_list:
        return {"value": 0, "details": []}
    result = {"value": 1, "details": []}
    for link in link_list:
        if not link.get("author_rights", False):
            result["value"] = 0
            result["details"].append(link["url"])
    return result


def evaluate_legal_aspects(
    legal_aspects: LegalAspectsSchema, link_list: list[dict]
) -> dict:
    legal_aspects_resume = get_schema_resume(legal_aspects.model_dump())
    legal_aspects_resume["author_metadata"] = check_author_rights(link_list)
    legal_aspects_resume["total"] = sum(
        v["value"] if isinstance(v, dict) else v for v in legal_aspects_resume.values()
    )
    return legal_aspects_resume
