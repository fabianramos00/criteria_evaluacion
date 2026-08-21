import httpx
from difflib import SequenceMatcher
from src.config.settings import settings
from src.core.http import get_sync_client


def is_similar(repository_name: str, repository_name2: str) -> bool:
    a = repository_name.strip().lower()
    b = repository_name2.strip().lower()
    return SequenceMatcher(None, a, b).ratio() >= settings.REPOSITORY_NAME_MIN_RATIO


def sum_resume(resume: dict) -> float:
    return sum(v["value"] if isinstance(v, dict) else v for v in resume.values())


def get_schema_resume(schema: dict) -> dict:
    resume = {}
    for key in schema:
        if key.endswith("_url"):
            continue
        url_key = f"{key}_url"
        value = 1 if schema[key] else 0
        if url_key in schema:
            resume[key] = {
                "value": value,
                "url": str(schema.get(url_key)) if value else None,
            }
        else:
            resume[key] = value
    return resume


def check_website(url: str) -> bool:
    try:
        response = get_sync_client().get(url, timeout=5)
        return response.status_code in (200, 301, 302)
    except httpx.RequestError:
        return False
