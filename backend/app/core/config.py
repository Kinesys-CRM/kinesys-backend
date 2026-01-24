import os
from pydantic_core.core_schema import FieldValidationInfo
from pydantic import PostgresDsn, EmailStr, AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_ai.models.openai import OpenAIModelName, OpenAIChatModelSettings, OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from typing import Any
import secrets
from enum import Enum

class ModeEnum(str, Enum):
    development = "development"
    production = "production"
    testing = "testing"

class Settings(BaseSettings):
    MODE: ModeEnum = ModeEnum.development
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str

    #* For JWT auth*
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    SECRET_KEY: str = secrets.token_urlsafe(32)

    # Database parts
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_NAME: str

    ASYNC_DATABASE_URI: PostgresDsn | str = ""

    @field_validator("ASYNC_DATABASE_URI", mode="after")
    def assemble_db_connection(cls, v: str | None, info: FieldValidationInfo) -> Any:
        if isinstance(v, str) and v == "":
            return PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=info.data.get("DATABASE_USER"),
                password=info.data.get("DATABASE_PASSWORD"),
                host=info.data.get("DATABASE_HOST"),
                port=info.data.get("DATABASE_PORT"),
                path=info.data.get("DATABASE_NAME"),
                query="ssl=require",
            )
        return v
    
    R2_ACCOUNT_ID: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET_NAME: str

    OPENAI_API_KEY: str

    VISION_MODEL_NAME: OpenAIModelName = "gpt-5"
    
    MODEL_TEMPERATURE: float = 0.1
    MODEL_TOP_P: float = 0.95

    model_config = SettingsConfigDict(case_sensitive=True, env_file="../.env")

settings = Settings()

default_model_settings = OpenAIChatModelSettings(
    temperature=settings.MODEL_TEMPERATURE,
    top_p=settings.MODEL_TOP_P
)

openai_provider = OpenAIProvider(api_key=settings.OPENAI_API_KEY)
vision_model = OpenAIChatModel(model_name=settings.VISION_MODEL_NAME, provider=openai_provider, settings=default_model_settings)