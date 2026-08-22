"""
Database schema management.
"""

from core.database import get_connection
from core.logger import get_logger

logger = get_logger(__name__)


def create_tables() -> None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            job_id TEXT UNIQUE NOT NULL,
            job_url TEXT NOT NULL,
            salary TEXT,
            description TEXT,
            employment_type TEXT,
            experience_level TEXT,
            posted_date TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()

    logger.info("Database schema created successfully.")