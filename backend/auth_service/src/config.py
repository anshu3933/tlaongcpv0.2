import os
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/auth_db")
    jwt_secret: str = os.getenv("JWT_SECRET", "development_secret_key")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_settings() -> Settings:
    """Get application settings"""
    return Settings()