import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    """
    APP_NAME: str = "Multi-Warehouse Occupancy Estimation Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    
    # Database URL configuration
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/warehouse_db"

    # Settings configurations
    model_config = SettingsConfigDict(
        # Load from .env if present. Resolve path relative to the file.
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings singleton
settings = Settings()
