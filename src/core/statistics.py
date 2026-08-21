import asyncio

import httpx

from src.api.schemas import StatisticsSchema
from src.core.http import get_async_client
from src.core.tools import get_schema_resume, sum_resume


async def statistics_url_exists(url: str) -> str | None:
    try:
        client = get_async_client()
        response = await client.get(url + "/statistics")
        if response.status_code < 400:
            return url + "/statistics"
        return None
    except httpx.ConnectError:
        return None


async def limited_statistics_url_exist(url: str) -> str | None:
    async with asyncio.Semaphore(5):
        return await statistics_url_exists(url)


async def evaluate_urls_statistics(link_list: list[dict]) -> dict:
    if not link_list:
        return {"value": 0, "details": []}
    tasks = [limited_statistics_url_exist(link["url"]) for link in link_list]
    results = await asyncio.gather(*tasks)
    value, details = 1, []
    for link, stat in zip(link_list, results):
        link["statistics"] = stat
        if stat is None:
            value = 0
            details.append(link["url"])
    return {"value": value, "details": details}


async def evaluate_statistics(
    statistics_schema: StatisticsSchema, link_list: list[dict]
) -> tuple[dict, list[dict]]:
    statistics_resume = get_schema_resume(statistics_schema.model_dump())
    statistics_resume["url_statistics"] = await evaluate_urls_statistics(link_list)
    statistics_resume["total"] = sum_resume(statistics_resume)
    return statistics_resume, link_list
