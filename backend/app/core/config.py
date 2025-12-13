from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, Field
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_title: str = Field(default="OpenRouter LLM Console", alias="APP_TITLE")
    app_origins: str = Field(default="http://localhost:5173", alias="APP_ORIGINS")
    db_path: str = Field(default="./console.db", alias="DB_PATH")

    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")
    openrouter_http_referer: str = Field(default="http://localhost:5173", alias="OPENROUTER_HTTP_REFERER")
    openrouter_x_title: str = Field(default="Self-Hosted LLM Console", alias="OPENROUTER_X_TITLE")

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.app_origins.split(",") if o.strip()]

settings = Settings()
