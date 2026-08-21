from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, AnyHttpUrl, field_validator, Field
from pydantic_core import PydanticCustomError
from src.core.tools import check_website


def validate_website_url(v):
    """Validate that a website URL is accessible"""
    if v is not None and not check_website(str(v)):
        raise ValueError("URL no accesible")
    return v


def validate_url_contains(url: str, base_url: Optional[str]) -> str:
    """Validate that url contains base_url"""
    if base_url is not None and base_url not in url:
        raise ValueError("The URL entered does not match the repository URL")
    return url


def conditional_required(condition_field: str, error_msg: str = "Field is required"):
    """Factory to create validators that require field when condition is true"""

    def validator(v, info):
        if info.data.get(condition_field) and not v:
            raise PydanticCustomError("missing_required", error_msg)
        return v

    return validator


def url_must_contain(base_url_field: str = "url"):
    """Factory to create validators that check URL contains base URL"""

    def validator(v, info):
        if v and info.data.get(base_url_field):
            validate_url_contains(str(v), info.data.get(base_url_field))
        return v

    return validator


def combined_validator(*validators):
    """Combine multiple validators into one"""

    def validator(v, info):
        for val_func in validators:
            v = val_func(v, info)
        return v

    return validator


class RegistrationSchema(BaseModel):
    repository_url: AnyHttpUrl
    repository_name: str = Field(..., min_length=1)
    repository_name1: str | None = None

    _validate_url = field_validator("repository_url")(validate_website_url)

    @field_validator("repository_name1")
    @classmethod
    def validate_names(cls, v, info):
        if v and info.data.get("repository_name") == v:
            raise PydanticCustomError("duplicate_names", "Duplicate names")
        return v

    @property
    def repository_names(self) -> list[str]:
        return [x for x in [self.repository_name, self.repository_name1] if x]


class VisibilitySchema(BaseModel):
    national_collector: bool
    initiatives_existence: bool
    collector_url1: AnyHttpUrl | None = None
    collector_url2: AnyHttpUrl | None = None
    collector_url3: AnyHttpUrl | None = None
    collector_url4: AnyHttpUrl | None = None
    collector_url5: AnyHttpUrl | None = None

    _validate_urls = field_validator(
        "collector_url1",
        "collector_url2",
        "collector_url3",
        "collector_url4",
        "collector_url5",
    )(validate_website_url)
    _validate_required = field_validator("collector_url1")(
        conditional_required("national_collector")
    )

    @property
    def collector_urls(self) -> list[AnyHttpUrl] | None:
        if not self.national_collector:
            return None
        return [
            str(url)
            for url in (
                self.collector_url1,
                self.collector_url2,
                self.collector_url3,
                self.collector_url4,
                self.collector_url5,
            )
            if url is not None
        ]


class PolicySchema(BaseModel):
    open_access: bool
    open_access_url: AnyHttpUrl | None = None
    metadata_reuse: bool
    metadata_reuse_url: AnyHttpUrl | None = None
    content_preservation: bool
    content_preservation_url: AnyHttpUrl | None = None
    deposit_data: bool
    deposit_data_url: AnyHttpUrl | None = None
    action_policy: bool
    action_policy_url: AnyHttpUrl | None = None
    policy_data: bool
    policy_data_url: AnyHttpUrl | None = None
    vision_mission: bool
    vision_mission_url: AnyHttpUrl | None = None
    contact: bool
    contact_url: AnyHttpUrl | None = None
    boai: bool

    _validate_urls = field_validator(
        "open_access_url",
        "metadata_reuse_url",
        "content_preservation_url",
        "deposit_data_url",
        "action_policy_url",
        "policy_data_url",
        "vision_mission_url",
        "contact_url",
    )(validate_website_url)

    _validate_open_access = field_validator("open_access_url")(
        conditional_required("open_access")
    )
    _validate_metadata_reuse = field_validator("metadata_reuse_url")(
        conditional_required("metadata_reuse")
    )
    _validate_content_preservation = field_validator("content_preservation_url")(
        conditional_required("content_preservation")
    )
    _validate_deposit_data = field_validator("deposit_data_url")(
        conditional_required("deposit_data")
    )

    _validate_action_policy = field_validator("action_policy_url")(
        combined_validator(conditional_required("action_policy"), url_must_contain())
    )
    _validate_policy_data = field_validator("policy_data_url")(
        combined_validator(conditional_required("policy_data"), url_must_contain())
    )
    _validate_vision_mission = field_validator("vision_mission_url")(
        combined_validator(conditional_required("vision_mission"), url_must_contain())
    )
    _validate_contact = field_validator("contact_url")(
        combined_validator(conditional_required("contact"), url_must_contain())
    )


class LegalAspectsSchema(BaseModel):
    author_property: bool
    author_permission: bool
    author_permission_url: AnyHttpUrl | None = None
    editorial_policy: bool
    author_copyright: bool

    _validate_url = field_validator("author_permission_url")(validate_website_url)
    _validate_required = field_validator("author_permission_url")(
        conditional_required("author_permission")
    )


class MetadataSchema(BaseModel):
    curation: bool
    classification_system: bool
    metadata_schema: bool
    metadata_export: bool


class InteroperabilitySchema(BaseModel):
    deleted_records: bool
    life_time: bool
    admin_email: bool
    identify_description: bool
    progressive_delivery: bool
    records_size: bool
    records_datestamp: bool
    systems_integration: bool
    share_data: bool


class SecuritySchema(BaseModel):
    backups: bool
    backups_url: AnyHttpUrl | None = None
    checksum: bool
    checksum_url: AnyHttpUrl | None = None
    backups_location: bool
    format_control: bool

    _validate_urls = field_validator("backups_url", "checksum_url")(
        validate_website_url
    )
    _validate_backups = field_validator("backups_url")(
        combined_validator(conditional_required("backups"), url_must_contain())
    )
    _validate_checksum = field_validator("checksum_url")(
        combined_validator(conditional_required("checksum"), url_must_contain())
    )


class StatisticsSchema(BaseModel):
    general_statistics: bool
    general_statistics_url: AnyHttpUrl | None = None
    save_logs: bool
    counter: bool
    url: str | None = None

    _validate_url = field_validator("general_statistics_url")(validate_website_url)
    _validate_required = field_validator("general_statistics_url")(
        combined_validator(
            conditional_required("general_statistics"), url_must_contain()
        )
    )


class ServicesSchema(BaseModel):
    rss_alert: bool
    author_profiles: bool
    author_profiles_url: AnyHttpUrl | None = None
    cite_metrics: bool
    cite_metrics_url: AnyHttpUrl | None = None
    new_metrics: bool
    new_metrics_url: AnyHttpUrl | None = None
    url: str | None = None

    _validate_urls = field_validator(
        "author_profiles_url", "cite_metrics_url", "new_metrics_url"
    )(validate_website_url)
    _validate_author_profiles = field_validator("author_profiles_url")(
        combined_validator(conditional_required("author_profiles"), url_must_contain())
    )
    _validate_cite_metrics = field_validator("cite_metrics_url")(
        combined_validator(conditional_required("cite_metrics"), url_must_contain())
    )
    _validate_new_metrics = field_validator("new_metrics_url")(
        combined_validator(conditional_required("new_metrics"), url_must_contain())
    )


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    repository_url: str
    repository_names: list[str]
    created_at: datetime
    updated_at: datetime
    rating: float
    last_item_evaluated: str
    is_completed: bool
