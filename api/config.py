"""
API Configuration
"""

from typing import List
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database
    db_path: Path = (
        Path(__file__).resolve().parents[1]
        / "output"
        / "job_hunter.duckdb"
    )

    # Default profile
    default_profile: str = "crm_manager"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()