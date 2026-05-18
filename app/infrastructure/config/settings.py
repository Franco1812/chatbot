from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("OPENAI_API_KEY", "openai_api_key"),
        description="Clave API de OpenAI para ChatOpenAI.",
    )
    redis_url: str = Field(
        default="",
        validation_alias=AliasChoices("REDIS_URL", "redis_url"),
        description="URL de Redis (ej. redis://localhost:6379/0).",
    )
    webhook_verify_token: str = Field(
        default="",
        validation_alias=AliasChoices("WEBHOOK_VERIFY_TOKEN", "webhook_verify_token"),
        description="Token secreto que Meta usa para verificar el webhook.",
    )
    tenants_file: str = Field(
        default="tenants.json",
        validation_alias=AliasChoices("TENANTS_FILE", "tenants_file"),
        description="Ruta al archivo JSON con la configuración de tiendas.",
    )
