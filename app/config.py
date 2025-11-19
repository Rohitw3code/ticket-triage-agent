# app/config.py

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "dev"
    DEBUG: bool = True
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: Optional[int] = None
    OPENAI_TIMEOUT: int = 60  # seconds
    
    # Retry Configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0  # seconds
    RETRY_BACKOFF: float = 2.0  # exponential backoff multiplier
    
    # App
    PORT: int = 8000
    MAX_DESCRIPTION_LENGTH: int = 5000
    LOG_LEVEL: str = "INFO"
    
    # KB
    KB_PATH: str = "kb/knowledge_base.json"
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"


class DevelopmentSettings(Settings):
    ENVIRONMENT: str = "dev"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    MAX_RETRIES: int = 2
    

class ProductionSettings(Settings):
    ENVIRONMENT: str = "prod"
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    MAX_RETRIES: int = 5
    CORS_ORIGINS: list = ["https://yourdomain.com"]


class TestingSettings(Settings):
    ENVIRONMENT: str = "test"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    MAX_RETRIES: int = 1


@lru_cache()
def get_settings() -> Settings:
    """Get settings based on environment variable."""
    env = os.getenv("ENVIRONMENT", "dev").lower()
    
    if env == "prod" or env == "production":
        return ProductionSettings()
    elif env == "test" or env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()