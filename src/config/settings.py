from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    OPEN_DOAR_URL: str = "https://v2.sherpa.ac.uk/cgi/retrieve"
    OPEN_DOAR_API_KEY: str
    R3DATA_URL: str = "https://www.re3data.org/api/beta/repositories"
    LA_REFERENCIA_URL: str = "https://www.lareferencia.info/vufind/Search/Results"
    OPEN_AIRE_URL: str = "https://api.openaire.eu/graph/v1"
    OPENALEX_URL: str = "https://api.openalex.org"
    BASE_URL: str = "https://www.base-search.net/Search/Results"
    CORE_URL: str = "https://api.core.ac.uk/v3"
    CORE_API_KEY: str
    BOAI_URL: str = "https://www.budapestopenaccessinitiative.org/sign/signatures/"
    FRIENDLY_URL_LENGTH: int = 40
    MIN_YEAR_DIFFERENCE: int = 5
    REPOSITORY_NAME_MIN_RATIO: float = 0.1

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
