import asyncio
from datetime import datetime
from re import compile

from bs4 import BeautifulSoup
import httpx

from src.api.schemas import MetadataSchema
from src.constants import (
    METADATA_DATE_REGEX,
    DATE_FORMATS,
    ACCESS_STANDARD_VALUES,
    RESULT_TYPES,
    FORMAT_DICT,
    VERSION_COAR_LIST,
    ISO_LANGUAGE_LIST,
    IRALIS_BASE_URL_ID,
    ORCID_BASE_URL_ID,
    METADATA_FIELDS,
    BIBLIOGRAPHIC_MANAGERS,
    METADATA_EXPORT_TYPES,
    SOCIAL_NETWORKS,
    FIELDS_ITEM,
)
from src.core.http import get_async_client
from src.core.tools import get_schema_resume, sum_resume


def check_metadata_date(
    page_parse: BeautifulSoup,
) -> tuple[dict[str, str] | None, bool | None]:
    date_dict = {}
    standard_date_format = True
    for regex in METADATA_DATE_REGEX:
        for meta in page_parse.find_all("meta", {"name": compile(regex)}):
            content = meta.get("content")
            name = meta.get("name")
            if not content or not name:
                continue
            date_dict[name] = content
            if standard_date_format:
                for fmt in DATE_FORMATS:
                    try:
                        datetime.strptime(content, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    standard_date_format = False
    return (date_dict or None), (standard_date_format or None)


def check_access_name(access_name_list: list[str] | None) -> str | None:
    if not access_name_list:
        return None
    match = set(access_name_list) & set(ACCESS_STANDARD_VALUES)
    return next(iter(match), None)


def check_types_research_result(dc_type_list: list[str] | None) -> list[str] | None:
    if not dc_type_list:
        return None
    values = [
        item
        for item in dc_type_list
        if any(result_type in item for result_type in RESULT_TYPES)
    ]
    return values or None


def check_format(format_list: list[str] | None) -> str | None:
    if not format_list:
        return None
    for fmt in format_list:
        parts = fmt.split("/")
        if (
            len(parts) == 2
            and parts[0] in FORMAT_DICT
            and parts[1] in FORMAT_DICT[parts[0]]
        ):
            return fmt
    return None


def check_version_format(metadata: list[str] | None) -> list[str] | None:
    if not metadata:
        return None
    matches = [item for item in metadata if any(v in item for v in VERSION_COAR_LIST)]
    return matches or None


def check_language_format(language_values: list[str] | None) -> str | None:
    if not language_values:
        return None
    for code, name in ISO_LANGUAGE_LIST:
        if code in language_values:
            return name
    if "zxx" in language_values:
        return "zxx"
    return None


def check_author_id(author_values: list[str] | None) -> str | None:
    if not author_values:
        return None
    if len(author_values) > 1:
        if all(
            IRALIS_BASE_URL_ID in v or ORCID_BASE_URL_ID in v for v in author_values
        ):
            return "ORCID/IraLIS"
        return None
    v = author_values[0]
    if IRALIS_BASE_URL_ID in v:
        return "IraLIS"
    if ORCID_BASE_URL_ID in v:
        return "ORCID"
    return None


def search_items(items: list[str], page: BeautifulSoup) -> dict[str, str | None] | None:
    result = {item: None for item in items}
    items_set = set(items)
    for a in page.find_all("a"):
        img_src = a.find("img")["src"] if a.find("img") else None
        for item in list(items_set):
            href = a.get("href", "")
            text = a.get_text(strip=True).lower()
            if item in href:
                result[item] = href
            elif item in text:
                result[item] = text
            elif img_src and item in img_src:
                result[item] = img_src
            else:
                continue
            items_set.remove(item)
    return result


async def get_metadata(link_dict: dict) -> dict:
    client = get_async_client(verify=False)
    try:
        page = await client.get(link_dict["url"])
    except httpx.RequestError:
        return link_dict
    page_parse = BeautifulSoup(page.content, "html.parser")
    metadata = {}
    for name in METADATA_FIELDS:
        meta_list = page_parse.find_all("meta", {"name": name})
        metadata[name] = [i["content"] for i in meta_list] if meta_list else None
    meta_identifier = page_parse.find_all(
        "meta", {"name": "DC.identifier", "scheme": "DCTERMS.URI"}
    )
    metadata["DC.identifier"] = (
        meta_identifier[0]["content"] if 1 == len(meta_identifier) else None
    )
    link_dict.update(
        {
            "dublin_core": True
            if 0 < len(page_parse.find_all("meta", {"name": compile(r"DC..*")}))
            else None,
            "standard_access_value": check_access_name(metadata["DC.rights"]),
            "standard_type_research_result": check_types_research_result(
                metadata["DC.type"]
            ),
            "standard_format": check_format(metadata["DC.format"]),
            "standard_version_coar": check_version_format(metadata["DC.type"]),
            "standard_language": check_language_format(metadata["DC.language"]),
            "author_id": check_author_id(metadata["DC.creator"]),
            "bibliographic_managers": search_items(BIBLIOGRAPHIC_MANAGERS, page_parse),
            "metadata_exports": search_items(METADATA_EXPORT_TYPES, page_parse),
            "social_networks": search_items(SOCIAL_NETWORKS, page_parse),
        }
    )
    metadata["DC.date"], link_dict["standard_date_format"] = check_metadata_date(
        page_parse
    )
    link_dict["single_type_research_result"] = (
        link_dict["standard_type_research_result"][0]
        if link_dict["standard_type_research_result"] is not None
        and len(link_dict["standard_type_research_result"]) == 1
        else None
    )
    link_dict["single_version"] = (
        link_dict["standard_version_coar"][0]
        if link_dict["standard_version_coar"] is not None
        and len(link_dict["standard_version_coar"]) == 1
        else None
    )
    link_dict["metadata"] = metadata
    return link_dict


def validate_metadata(url_dict_list: list[dict]) -> tuple[dict, dict]:
    fields_metadata_dict = {
        f: {"value": True, "details": []} for f in METADATA_FIELDS + ["DC.date"]
    }
    fields_dict = {f: {"value": 1, "details": []} for f in FIELDS_ITEM}
    for url_dict in url_dict_list:
        for f in fields_metadata_dict:
            if url_dict["metadata"].get(f) is None:
                fields_metadata_dict[f]["value"] = False
                fields_metadata_dict[f]["details"].append(url_dict["url"])
        for f in fields_dict:
            if url_dict.get(f) is None:
                fields_dict[f]["value"] = 0
                fields_dict[f]["details"].append(url_dict["url"])
    return fields_metadata_dict, fields_dict


def evaluate_metadata_group(metadata_dict: dict, fields: list[str]) -> dict:
    details = {f: metadata_dict[f] for f in fields}
    value = 0 if any(not metadata_dict[f]["value"] for f in fields) else 1
    return {"value": value, "details": details}


async def limited_get_metadata(link: dict) -> dict | None:
    async with asyncio.Semaphore(5):
        return await get_metadata(link)


async def evaluate_metadata(
    metadata_schema: MetadataSchema, link_list: list[dict]
) -> tuple[dict, list[dict]]:
    metadata_resume = get_schema_resume(metadata_schema.model_dump())
    new_link_list = await asyncio.gather(
        *(limited_get_metadata(link) for link in link_list)
    )
    result_metadata, result_fields = validate_metadata(new_link_list)
    metadata_resume["first_fields"] = evaluate_metadata_group(
        result_metadata, ["DC.creator", "DC.title", "DC.type", "DC.date", "DC.rights"]
    )
    metadata_resume["second_fields"] = evaluate_metadata_group(
        result_metadata,
        [
            "DC.description",
            "DC.format",
            "DC.language",
            "DC.identifier",
            "DC.subject",
            "DC.contributor",
            "DC.relation",
            "DC.publisher",
        ],
    )
    metadata_resume.update(result_fields)
    metadata_resume["total"] = sum_resume(metadata_resume)
    return metadata_resume, new_link_list
