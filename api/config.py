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
        / "job_hunter_api.duckdb"
    )

    # Authentication
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Google OAuth
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None
    frontend_url: str = "https://aijobhunter.in"

    # Default profile
    default_profile: str = "crm_manager"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()