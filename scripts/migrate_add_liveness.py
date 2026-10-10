#!/usr/bin/env python3
"""
One-time migration: add job liveness columns to fact_jobs.

Adds:
  - is_active          BOOLEAN   — FALSE means stale/dead, hide from users
  - last_seen_at       TIMESTAMP — last time pipeline saw this job
  - url_status         VARCHAR   — 'ok' | 'dead' | 'unknown' (background worker)
  - url_checked_at     TIMESTAMP — last time URL was HEAD-checked
  - reported_dead_count INTEGER  — how many users marked this dead

Safe to re-run — checks column existence first.
Backfills existing rows: last_seen_at = NOW(), is_active = TRUE.
"""

from __future__ import annotations

from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
MASTER_DB = ROOT / "output" / "job_hunter.duckdb"

NEW_COLUMNS = [
    ("is_active", "BOOLEAN DEFAULT TRUE"),
    ("last_seen_at", "TIMESTAMP"),
    ("url_status", "VARCHAR DEFAULT 'unknown'"),
    ("url_checked_at", "TIMESTAMP"),
    ("reported_dead_count", "INTEGER DEFAULT 0"),
]


def existing_columns(con: duckdb.DuckDBPyConnection) -> set[str]:
    rows = con.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'fact_jobs'
        """
    ).fetchall()
    return {row[0] for row in rows}


def main() -> int:
    if not MASTER_DB.exists():
        raise FileNotFoundError(f"Master DB not found: {MASTER_DB}")

    print(f"Target DB: {MASTER_DB}")
    print()

    con = duckdb.connect(str(MASTER_DB))

    before_count = con.execute(
        "SELECT COUNT(*) FROM fact_jobs"
    ).fetchone()[0]
    print(f"fact_jobs rows before: {before_count:,}")
    print()

    current = existing_columns(con)
    print(f"Existing columns ({len(current)}):")
    for col in sorted(current):
        print(f"  - {col}")
    print()

    added = 0
    for col_name, col_type in NEW_COLUMNS:
        if col_name in current:
            print(f"SKIP  {col_name} (already exists)")
            continue

        sql = f"ALTER TABLE fact_jobs ADD COLUMN {col_name} {col_type}"
        print(f"ADD   {col_name}: {sql}")
        con.execute(sql)
        added += 1

    print()
    print(f"Columns added: {added}")
    print()

    if added > 0:
        print("Backfilling existing rows...")
        con.execute(
            """
            UPDATE fact_jobs
            SET last_seen_at = NOW()
            WHERE last_seen_at IS NULL
            """
        )
        con.execute(
            """
            UPDATE fact_jobs
            SET is_active = TRUE
            WHERE is_active IS NULL
            """
        )
        con.execute(
            """
            UPDATE fact_jobs
            SET url_status = 'unknown'
            WHERE url_status IS NULL
            """
        )
        con.execute(
            """
            UPDATE fact_jobs
            SET reported_dead_count = 0
            WHERE reported_dead_count IS NULL
            """
        )
        print("Backfill complete.")
        print()

    after_count = con.execute(
        "SELECT COUNT(*) FROM fact_jobs"
    ).fetchone()[0]
    print(f"fact_jobs rows after:  {after_count:,}")

    con.execute("CHECKPOINT")
    con.close()

    print()
    print("✓ Migration complete.")
    print()
    print("Next: verify with:")
    print(
        "  python3 -c \"import duckdb; "
        "con=duckdb.connect('output/job_hunter.duckdb', read_only=True); "
        "print(con.execute('SELECT is_active, COUNT(*) FROM fact_jobs GROUP BY is_active').fetchall())\""
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
