import asyncio
import re
from collections.abc import Callable
from datetime import date
from xml.etree.ElementTree import fromstring

from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
import httpx
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import VisibilitySchema
from src.config.settings import settings
from src.core.http import get_async_client
from src.core.tools import is_similar, sum_resume
from src.database.models import OAI_PMH, ROAR, Record


async def get_open_doar_data(repository_name: str) -> dict | None:
    params = {
        "item-type": "repository",
        "api-key": settings.OPEN_DOAR_API_KEY,
        "format": "Json",
        "filter": f'[["name","contains word","{repository_name}"]]',
        "limit": 4,
    }
    client = get_async_client(verify=False)
    response = await client.get(settings.OPEN_DOAR_URL, params=params)
    data = response.json()
    return (
        {
            "name": data["items"][0]["repository_metadata"]["name"][0]["name"],
            "host": data["items"][0]["repository_metadata"]["url"],
        }
        if 0 < len(data["items"])
        else None
    )


async def get_roar_data(db: AsyncSession, repository_names: list[str]) -> dict | None:
    conditions = [ROAR.repository_name.ilike(f"%{name}%") for name in repository_names]
    result_roar = await db.execute(select(ROAR).filter(or_(*conditions)))
    result_roar = result_roar.scalars().first()
    return (
        {"name": result_roar.repository_name, "host": result_roar.home_page}
        if result_roar
        else None
    )


async def get_oai_pmh_data(
    db: AsyncSession, repository_names: list[str]
) -> dict | None:
    conditions = [
        OAI_PMH.repository_name.ilike(f"%{name}%") for name in repository_names
    ]
    result_oai = await db.execute(select(OAI_PMH).filter(or_(*conditions)))
    result_oai = result_oai.scalars().first()
    return (
        {"name": result_oai.repository_name, "host": result_oai.namespace_identifier}
        if result_oai
        else None
    )


async def get_re3data(repository_name: str) -> dict | None:
    URL_R3DATA = f"{settings.R3DATA_URL}?query={repository_name}"
    client = get_async_client()
    response_re3data = await client.get(URL_R3DATA)
    tree = fromstring(response_re3data.content)
    for i in tree:
        if is_similar(i.find("name").text, repository_name):
            return {"name": i.find("name").text, "host": None}
    return None


async def get_la_referencia_links(repository_name: str) -> list[str]:
    params = {
        "limit": 5,
        "filter[]": f'reponame_str:"{repository_name}"',
        "type": "AllFields",
        "sort": "year",
    }
    client = get_async_client()
    try:
        page_la = await client.get(
            settings.LA_REFERENCIA_URL, params=params, timeout=10
        )
    except (httpx.ConnectTimeout, httpx.ReadTimeout):
        return []
    page_parser_la = BeautifulSoup(page_la.content, "html.parser")
    la_links = [
        i.find_all("a")[0]["href"]
        for i in page_parser_la.find_all("div", {"class": "result"})
    ]

    semaphore = asyncio.Semaphore(5)

    async def fetch_link(path: str) -> str:
        async with semaphore:
            page_la = await client.get("https://www.lareferencia.info" + path)
            page_parser_la_r = BeautifulSoup(page_la.content, "html.parser")
            return page_parser_la_r.find_all("tr")[-4].find("a")["href"]

    return await asyncio.gather(*(fetch_link(i) for i in la_links))


async def get_la_referencia(repository_name: str) -> dict | None:
    params = {
        "lookfor": repository_name,
        "type": "AllFields",
        "limit": 10,
    }
    client = get_async_client()
    try:
        page_la = await client.get(
            settings.LA_REFERENCIA_URL, params=params, timeout=10
        )
    except (httpx.ConnectTimeout, httpx.ReadTimeout):
        return None
    page_parser_la = BeautifulSoup(page_la.content, "html.parser")
    for i in page_parser_la.find_all("div", {"class": "result"}):
        repository_la = i.find_all("a")[3].text
        if is_similar(repository_la, repository_name):
            return {
                "name": repository_la,
                "host": None,
                "links": await get_la_referencia_links(repository_la),
            }
    return None


async def get_open_aire_links(data_source_id: str, repository_url: str) -> list:
    links_oa = []
    client = get_async_client()
    params: dict = {
        "relHostingDataSourceId": data_source_id,
        "page": 1,
        "pageSize": 10,
        "fromPublicationDate": (
            date.today() - relativedelta(years=settings.MIN_YEAR_DIFFERENCE)
        ).strftime("%Y"),
    }
    response_oa = await client.get(
        f"{settings.OPEN_AIRE_URL}/researchProducts", params=params
    )
    if response_oa.status_code != 200:
        return []
    data_oa = response_oa.json()
    links_oa = [
        url
        for i in data_oa.get("results", [])
        for instance in i.get("instances", [])
        for url in instance.get("urls", [])
        if repository_url in url
    ]
    return links_oa


async def get_open_aire_data(repository_name: str) -> dict | None:
    client = get_async_client()
    params: dict = {
        "search": repository_name,
        "page": 1,
        "pageSize": 10,
        "dataSourceTypeName": "Institutional Repository",
    }
    response_oa = await client.get(
        f"{settings.OPEN_AIRE_URL}/dataSources", params=params
    )
    if response_oa.status_code != 200:
        return None
    data_oa = response_oa.json()
    for datasource in data_oa["results"]:
        if is_similar(datasource["officialName"], repository_name):
            return {
                "name": datasource["officialName"],
                "host": datasource.get("websiteUrl"),
                "links": await get_open_aire_links(
                    datasource["id"], datasource.get("websiteUrl")
                ),
            }
    return None


async def get_open_alex_data(repository_url: str) -> dict | None:
    repository_url = (
        repository_url.replace("https://", "").replace("http://", "").rstrip("/")
    )
    five_years_ago = date.today() - relativedelta(years=settings.MIN_YEAR_DIFFERENCE)
    params = {
        "per_page": 50,
        "filter": f'from_publication_date:{five_years_ago.strftime("%Y-%m-%d")}',
        "search": repository_url,
    }
    try:
        client = get_async_client()
        api_result = await client.get(f"{settings.OPENALEX_URL}/works", params=params)
        data = api_result.json()
    except httpx.HTTPError:
        return None
    results = []
    for work in data.get("results", []):
        landing_url = work.get("primary_location", {}).get("landing_page_url", "")
        if repository_url in landing_url:
            results.append(
                {
                    "title": work.get("title"),
                    "landing_page": landing_url,
                }
            )

    if results:
        return {
            "name": None,
            "host": repository_url,
            "links": [r["landing_page"] for r in results],
        }

    return None


# TODO: Implement
# async def get_base_data(repository_name: str):
#     async with httpx.AsyncClient() as client:
#         page_base = await client.get(f'{settings.BASE_URL}?lookfor={repository_name}')
#         page_parser_base = BeautifulSoup(page_base.content, 'html.parser')
#         base_repository = None
#         art_list = []
#         for i in page_parser_base.find_all('div', {'class': 'record-panel panel panel-default'}):
#             repository_tmp = \
#                 i.find('div', {'class': 'panel-body'}).find_all('div', {'class': 'row row-eq-height'})[-4:-3][0].find_all(
#                     'div')[1].find(text=True, recursive=False)
#             repository_tmp = repository_tmp.rstrip().lstrip()
#             ratio = SequenceMatcher(None, repository_tmp.lower(), repository_name.lower()).ratio()
#             art_list.append((repository_tmp, i.find('a', {'class': 'link1'})['href']))
#             if 0.9 > ratio:
#                 continue
#             if base_repository is None or base_repository['ratio'] < ratio:
#                 base_repository = {'name': repository_tmp, 'host': None, 'ratio': ratio}
#         if base_repository is not None:
#             base_repository['links'] = [i[1] for i in art_list if base_repository['name'] == i[0]]
#         return base_repository


async def get_core_data(repository_name: str) -> dict | None:
    client = get_async_client()
    core_response = await client.get(
        f"{settings.CORE_URL}/search/data-providers/",
        params={"q": f"name:{repository_name}"},
        headers={"Authorization": f"Bearer {settings.CORE_API_KEY}"},
    )
    if core_response.status_code != 200:
        return None
    core_result = core_response.json()
    for data_provider in core_result["results"]:
        if data_provider.get("type") != "REPOSITORY":
            continue
        if is_similar(data_provider.get("name"), repository_name):
            return {
                "name": data_provider.get("name"),
                "host": data_provider.get("homepageUrl"),
            }
    return None


def standard_name(data: dict) -> dict:
    names = [v["name"] for v in data.values() if v and v.get("name") is not None]
    if not names:
        return {"value": 1.5, "details": names}
    value = 1.5 if len(set(names)) == 1 else 0
    return {"value": value, "details": names}


def friendly_secure_url(repository_url: str) -> dict:
    if "https" not in repository_url:
        return {"text": "Insecure URL", "value": 0}
    host_clear = repository_url.replace("https://", "")
    if len(host_clear) > settings.FRIENDLY_URL_LENGTH or not re.match(
        r"^[a-z0-9.-/]+$", host_clear
    ):
        return {"text": "Not a friendly URL", "value": 0}
    return {"text": "Friendly and secure URL", "value": 1.5}


def count_items(data: dict, item_name: str) -> dict:
    count = sum(v is not None for v in data.values())
    if count == 0:
        return {"value": 0, "text": f"Not present in {item_name}"}
    if count == len(data):
        return {"value": 1.5, "text": f"Presence in {count} {item_name}"}
    return {"value": 1, "text": f"Presence in 1 or more {item_name}"}


def count_national_collectors(collector_data: list[str] | None) -> dict:
    if collector_data is None:
        return {"value": 0, "text": "Not present in national collectors", "details": []}
    if 5 == len(collector_data):
        return {
            "value": 1.5,
            "text": "Presence in 5 national collectors",
            "details": collector_data,
        }
    return {
        "value": 1,
        "text": "Presence in 1 or more national collectors",
        "details": collector_data,
    }


async def search_in(
    function: Callable[..., dict | None], repository_names: list[str]
) -> dict | None:
    for i in repository_names:
        result = await function(i)
        if result is not None:
            return result
    return None


async def is_open_access(url: str) -> dict | None:
    try:
        client = get_async_client()
        page = await client.get(url)
    except httpx.RequestError:
        return None
    soup = BeautifulSoup(page.content, "html.parser")
    meta_list = soup.find_all("meta", {"name": "DC.rights"})

    is_open = any("openAccess" in meta.get("content", "") for meta in meta_list)
    author_rights = bool(meta_list)

    return {"url": url, "open_access": is_open, "author_rights": author_rights}


async def limited_is_open_access(url: str) -> dict | None:
    async with asyncio.Semaphore(5):
        return await is_open_access(url)


async def open_access(visibility_dict: dict) -> tuple[dict, list]:
    dict_list, value = [], 1
    link_list = [
        link
        for v in visibility_dict.values()
        if v and "links" in v
        for link in v["links"]
    ]
    tasks = [limited_is_open_access(link) for link in link_list]
    result = await asyncio.gather(*tasks)
    for i in result:
        if i is None:
            value = 0
            continue
        if not i["open_access"]:
            link_list.remove(i["url"])
            value = 0
        dict_list.append(i)
    return {"value": value, "details": link_list}, dict_list


async def execute_async_search(
    func_dict: dict[str, Callable], repository_name_list: list[str]
) -> dict:
    tasks = (search_in(func_dict[key], repository_name_list) for key in func_dict)
    results = await asyncio.gather(*tasks)
    return dict(zip(func_dict.keys(), results))


async def evaluate_visibility(
    db: AsyncSession, record: Record, visibility_schema: VisibilitySchema
) -> tuple[dict, list]:
    repository_names: list = record.repository_names
    functions_dict: dict = {
        "OpenDoar": get_open_doar_data,
        "re3data": get_re3data,
        "LA-Referencia": get_la_referencia,
        "OpenAIRE": get_open_aire_data,
        # 'BASE': get_base_data
        "CORE": get_core_data,
    }
    result_pool: dict = await execute_async_search(functions_dict, repository_names)
    resume_visibility = {
        "directory": {
            "details": {
                "OpenDoar": result_pool["OpenDoar"],
                "ROAR": await get_roar_data(db, repository_names),
                "OAI-PMH": await get_oai_pmh_data(db, repository_names),
                "re3data": result_pool["re3data"],
            }
        },
        "collector": {
            "details": {
                "LA-Referencia": result_pool["LA-Referencia"],
                "OpenAIRE": result_pool["OpenAIRE"],
                "OpenAlex": await get_open_alex_data(record.repository_url),
                "BASE": None,  # result_pool['BASE'],
                "CORE": result_pool["CORE"],
            }
        },
        "initiatives_existence": 1 if visibility_schema.initiatives_existence else 0,
        "national_collector": count_national_collectors(
            visibility_schema.collector_urls
        ),
        "url": friendly_secure_url(record.repository_url),
    }
    data_links: dict = (
        resume_visibility["directory"]["details"].copy()
        | resume_visibility["collector"]["details"].copy()
    )
    resume_visibility["standard"] = standard_name(data_links)
    resume_visibility["directory"].update(
        count_items(resume_visibility["directory"]["details"], "national directories")
    )
    resume_visibility["collector"].update(
        count_items(
            resume_visibility["collector"]["details"], "international collectors"
        )
    )
    resume_visibility["open_access"], links_dict = await open_access(data_links)
    resume_visibility["total"] = sum_resume(resume_visibility)
    return resume_visibility, links_dict
