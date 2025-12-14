from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_title: str = Field(default="OpenRouter LLM Console", alias="APP_TITLE")
    app_origins: str = Field(default="http://localhost:5173", alias="APP_ORIGINS")
    db_path: str = Field(default="./console.db", alias="DB_PATH")
    uploads_dir: str = Field(default="./uploads", alias="UPLOADS_DIR")

    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_timeout: int = Field(default=90, alias="OPENROUTER_TIMEOUT")
    
    # Rate limiting configuration (requests per time period)
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    
    # Critical resource-intensive endpoints
    rate_limit_stream: str = Field(default="20 per minute", alias="RATE_LIMIT_STREAM")
    rate_limit_model_sync: str = Field(default="60 per hour", alias="RATE_LIMIT_MODEL_SYNC")
    rate_limit_upload: str = Field(default="50 per minute", alias="RATE_LIMIT_UPLOAD")
    
    # Standard CRUD operations
    rate_limit_sessions: str = Field(default="60 per minute", alias="RATE_LIMIT_SESSIONS")
    rate_limit_messages: str = Field(default="100 per minute", alias="RATE_LIMIT_MESSAGES")
    rate_limit_profiles: str = Field(default="60 per minute", alias="RATE_LIMIT_PROFILES")
    
    # Read-only operations
    rate_limit_models_list: str = Field(default="120 per minute", alias="RATE_LIMIT_MODELS_LIST")
    rate_limit_usage_logs: str = Field(default="120 per minute", alias="RATE_LIMIT_USAGE_LOGS")
    rate_limit_health_check: str = Field(default="300 per minute", alias="RATE_LIMIT_HEALTH_CHECK")

    @field_validator('openrouter_api_key')
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate OpenRouter API key format and presence."""
        if not v or v.strip() == "":
            logger.warning(
                "OPENROUTER_API_KEY is not set. API calls will fail."
            )
            return ""
        
        v = v.strip()
        
        # OpenRouter keys follow pattern: sk-or-v1-*
        if not v.startswith("sk-or-v1-"):
            raise ValueError(
                "Invalid OPENROUTER_API_KEY format. Expected format: sk-or-v1-*"
            )
        
        # Minimum realistic key length (prefix + some content)
        if len(v) < 20:
            raise ValueError(
                "OPENROUTER_API_KEY appears too short. Check your key."
            )
        
        logger.info("OPENROUTER_API_KEY validated successfully")
        return v
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")
    openrouter_http_referer: str = Field(default="http://localhost:5173", alias="OPENROUTER_HTTP_REFERER")
    openrouter_x_title: str = Field(default="Self-Hosted LLM Console", alias="OPENROUTER_X_TITLE")

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.app_origins.split(",") if o.strip()]

settings = Settings()
