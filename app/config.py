# app/config.py

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # App
    PORT: int = 8000
    MAX_DESCRIPTION_LENGTH: int = 5000
    
    # KB
    KB_PATH: str = "kb/knowledge_base.json"
    
    class Config:
        env_file = ".env"


def get_settings():
    return Settings()