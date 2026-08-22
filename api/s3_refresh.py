from __future__ import annotations

import hashlib
import shutil
import time
from pathlib import Path

import boto3
import duckdb

from api.config import settings


S3_BUCKET = "ai-job-hunter-production-db"
S3_KEY = "job_hunter.duckdb"
CHECK_INTERVAL_SECONDS = 30

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "output" / "job_hunter.duckdb"
TMP_PATH = ROOT / "output" / "job_hunter.duckdb.tmp"


def _etag() -> str | None:
    s3 = boto3.client("s3")
    response = s3.head_object(
        Bucket=S3_BUCKET,
        Key=S3_KEY,
    )
    return str(response.get("ETag", "")).strip('"') or None


def _download_and_validate() -> None:
    s3 = boto3.client("s3")

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    s3.download_file(
        S3_BUCKET,
        S3_KEY,
        str(TMP_PATH),
    )

    con = duckdb.connect(
        str(TMP_PATH),
        read_only=True,
    )

    required = {
        "fact_jobs",
        "fact_job_scores",
        "fact_jobs_skills",
        "dim_company",
        "dim_location",
        "dim_skill",
        "search_session",
    }

    tables = {
        row[0]
        for row in con.execute(
            "SHOW TABLES"
        ).fetchall()
    }

    missing = required - tables

    if missing:
        con.close()
        TMP_PATH.unlink(missing_ok=True)
        raise RuntimeError(
            f"S3 DB missing tables: {sorted(missing)}"
        )

    jobs = con.execute(
        "SELECT COUNT(*) FROM fact_jobs"
    ).fetchone()[0]

    if jobs <= 0:
        con.close()
        TMP_PATH.unlink(missing_ok=True)
        raise RuntimeError(
            "S3 DB contains zero jobs"
        )

    con.close()

    TMP_PATH.replace(DB_PATH)


def refresh_loop() -> None:
    last_etag: str | None = None

    while True:
        try:
            current = _etag()

            if current and current != last_etag:
                _download_and_validate()
                last_etag = current

        except Exception as exc:
            print(
                f"S3 refresh failed: {exc}",
                flush=True,
            )

        time.sleep(
            CHECK_INTERVAL_SECONDS
        )
