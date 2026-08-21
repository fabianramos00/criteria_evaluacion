from src.api.schemas import ServicesSchema
from src.core.tools import get_schema_resume, sum_resume
from src.constants import BIBLIOGRAPHIC_MANAGERS, METADATA_EXPORT_TYPES, SOCIAL_NETWORKS


def evaluate_items(links: list[dict], items_dict: dict) -> dict:
    if not links:
        return {key: 0 for key in items_dict}
    values = {key: 1 for key in items_dict}
    for link in links:
        for key in list(items_dict.keys()):
            field_list, threshold = items_dict[key]
            count = sum(
                1 for field in field_list if link.get(key, {}).get(field) is not None
            )
            if count >= threshold:
                continue
            elif count == 0:
                values[key] = 0
                del items_dict[key]
            else:
                values[key] = 0.5
        if not items_dict:
            break
    return values


def evaluate_services(services_schema: ServicesSchema, link_list: list[dict]) -> dict:
    services_resume = get_schema_resume(services_schema.model_dump())
    evaluated_items = evaluate_items(
        link_list,
        {
            "bibliographic_managers": (BIBLIOGRAPHIC_MANAGERS, 2),
            "metadata_exports": (METADATA_EXPORT_TYPES, 2),
            "social_networks": (SOCIAL_NETWORKS, 2),
        },
    )
    for key, value in evaluated_items.items():
        services_resume[key] = value
    services_resume["total"] = sum_resume(services_resume)
    return services_resume
