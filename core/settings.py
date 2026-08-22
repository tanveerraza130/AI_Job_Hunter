"""
Application settings.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

DATABASE_PATH = BASE_DIR / "ai_job_hunter.db"

DEBUG = True
LOG_LEVEL = "INFO"