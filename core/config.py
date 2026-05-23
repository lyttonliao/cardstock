from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    aws_access_key_id:      str | None = None
    aws_secret_access_key:  str | None = None
    aws_default_region:     str = "us-east-2"
    s3_bucket:              str | None = None
    pokemon_tcg_api_key:    str | None = None

    algolia_application_id: str | None = None
    algolia_search_api_key: str | None = None
    algolia_write_api_key:  str | None = None

settings = Settings()
