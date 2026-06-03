from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file so it's found regardless of CWD
_ENV_FILE = Path(__file__).parent.parent / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")
    aws_access_key_id:      str | None = None
    aws_secret_access_key:  str | None = None
    aws_default_region:     str = "us-east-2"
    s3_bucket:              str | None = None
    pokemon_tcg_api_key:    str | None = None

    algolia_application_id: str | None = None
    algolia_search_api_key: str | None = None
    algolia_write_api_key:  str | None = None

settings = Settings()
