"""
Local file watcher for the API database.

Replaces the previous S3-based refresh. Watches the production
minimal snapshot and copies it into the API's runtime cache
when its mtime or size changes.

- Reads:   output/job_hunter_production_minimal.duckdb
- Writes:  output/job_hunter_api.duckdb
- Never touches the master DB (output/job_hunter.duckdb).
"""
from __future__ import annotations

import shutil
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "output" / "job_hunter_production_minimal.duckdb"
API_PATH = ROOT / "output" / "job_hunter_api.duckdb"
TMP_PATH = ROOT / "output" / "job_hunter_api.duckdb.tmp"
MASTER_DB_PATH = ROOT / "output" / "job_hunter.duckdb"
CHECK_INTERVAL_SECONDS = 30

if API_PATH == MASTER_DB_PATH:
    raise RuntimeError("FATAL: API cache must never be the Master DB")


def _signature(path: Path) -> tuple[int, int] | None:
    if not path.exists():
        return None
    st = path.stat()
    return (st.st_mtime_ns, st.st_size)


def _validate(db: Path) -> None:
    con = duckdb.connect(str(db), read_only=True)
    try:
        required = {
            "fact_jobs", "fact_job_scores", "fact_jobs_skills",
            "dim_company", "dim_location", "dim_skill",
            "search_session",
        }
        tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
        missing = required - tables
        if missing:
            raise RuntimeError(f"Snapshot missing tables: {sorted(missing)}")
        jobs = con.execute("SELECT COUNT(*) FROM fact_jobs").fetchone()[0]
        if jobs <= 0:
            raise RuntimeError("Snapshot contains zero jobs")
    finally:
        con.close()


def _sync() -> None:
    shutil.copyfile(SOURCE_PATH, TMP_PATH)
    _validate(TMP_PATH)
    TMP_PATH.replace(API_PATH)


def refresh_loop() -> None:
    last_sig: tuple[int, int] | None = None
    while True:
        try:
            sig = _signature(SOURCE_PATH)
            if sig is None:
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue
            if sig != last_sig:
                _sync()
                last_sig = sig
                print(f"API cache reloaded from {SOURCE_PATH.name}", flush=True)
        except Exception as exc:
            print(f"API refresh failed: {exc}", flush=True)
        time.sleep(CHECK_INTERVAL_SECONDS)
