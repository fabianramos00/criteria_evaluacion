import httpx
from difflib import SequenceMatcher
from src.config.settings import settings


def is_similar(repository_name: str, repository_name2: str) -> bool:
    a = repository_name.strip().lower()
    b = repository_name2.strip().lower()
    return SequenceMatcher(None, a, b).ratio() >= settings.REPOSITORY_NAME_MIN_RATIO


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
                "url": str(schema.get(url_key)) if value else None
            }
        else:
            resume[key] = value
    return resume


def check_website(url: str) -> bool:
    try:
        response = httpx.get(url, verify=False, timeout=5)
        return response.status_code in (200, 301, 302)
    except httpx.RequestError:
        return False
        