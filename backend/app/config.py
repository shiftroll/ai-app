"""
Application configuration using pydantic-settings.
Loads from environment variables with sensible defaults.
"""

import os
from typing import Optional, List
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment"""

    # App
    app_name: str = "Crafta Control Room"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")

    # Database
    database_url: str = Field(
        default="postgresql://crafta:crafta@localhost:5432/crafta",
        alias="DATABASE_URL"
    )
    database_pool_size: int = Field(default=5, alias="DATABASE_POOL_SIZE")

    # Redis
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    # Security
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        alias="SECRET_KEY"
    )
    encryption_key: str = Field(
        default="dev-encryption-key-32bytes!!!",  # 32 bytes
        alias="ENCRYPTION_KEY"
    )

    # RSA Keys for signing
    rsa_private_key: Optional[str] = Field(default=None, alias="RSA_PRIVATE_KEY")
    rsa_public_key: Optional[str] = Field(default=None, alias="RSA_PUBLIC_KEY")

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # LLM
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    llm_model: str = Field(default="gpt-4-turbo-preview", alias="LLM_MODEL")

    # ERP Connectors
    quickbooks_client_id: Optional[str] = Field(default=None, alias="QUICKBOOKS_CLIENT_ID")
    quickbooks_client_secret: Optional[str] = Field(default=None, alias="QUICKBOOKS_CLIENT_SECRET")
    quickbooks_redirect_uri: Optional[str] = Field(default=None, alias="QUICKBOOKS_REDIRECT_URI")

    xero_client_id: Optional[str] = Field(default=None, alias="XERO_CLIENT_ID")
    xero_client_secret: Optional[str] = Field(default=None, alias="XERO_CLIENT_SECRET")
    xero_redirect_uri: Optional[str] = Field(default=None, alias="XERO_REDIRECT_URI")

    netsuite_account_id: Optional[str] = Field(default=None, alias="NETSUITE_ACCOUNT_ID")
    netsuite_consumer_key: Optional[str] = Field(default=None, alias="NETSUITE_CONSUMER_KEY")
    netsuite_consumer_secret: Optional[str] = Field(default=None, alias="NETSUITE_CONSUMER_SECRET")

    # File Storage
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    max_file_size_mb: int = Field(default=50, alias="MAX_FILE_SIZE_MB")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # HITL Rules
    confidence_threshold: float = 0.80  # Below this = exception
    require_cfo_for_rev_rec: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Create settings instance
settings = get_settings()
