"""
Repository for job database operations.
"""

import sqlite3

from core.database import get_connection
from jobs.models import Job


class JobRepository:

    def __init__(self):
        self.connection = get_connection()

    def save(self, job: Job):

        self.connection.execute(
            """
            INSERT OR IGNORE INTO jobs (
                job_id,
                source,
                title,
                company,
                location,
                job_url,
                salary,
                description,
                employment_type,
                experience_level,
                posted_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.job_id,
                job.source,
                job.title,
                job.company,
                job.location,
                job.job_url,
                job.salary,
                job.description,
                job.employment_type,
                job.experience_level,
                job.posted_date,
            ),
        )

        self.connection.commit()

    def get_all(self) -> list[sqlite3.Row]:

        cursor = self.connection.execute(
            """
            SELECT *
            FROM jobs
            ORDER BY id DESC
            """
        )

        return cursor.fetchall()

    def close(self):

        self.connection.close()