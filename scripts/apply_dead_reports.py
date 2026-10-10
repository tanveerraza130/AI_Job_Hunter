#!/usr/bin/env python3
"""
Apply user dead-job reports to the Master DB.

Reads:   data/application.duckdb  (user reports)
Writes:  output/job_hunter.duckdb (fact_jobs.is_active + reported_dead_count)

Rule:
  - Count DISTINCT users per job_id with reported_dead_at IS NOT NULL
  - If count >= THRESHOLD (default 5), mark fact_jobs.is_active = FALSE
    and store reported_dead_count

Safe to run repeatedly. Idempotent.

Usage:
  python3 scripts/apply_dead_reports.py
  python3 scripts/apply_dead_reports.py --dry-run
  python3 scripts/apply_dead_reports.py --threshold 3
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
MASTER_DB = ROOT / "output" / "job_hunter.duckdb"
APPS_DB = ROOT / "data" / "application.duckdb"
DEFAULT_THRESHOLD = 5


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    args = parser.parse_args()

    if not MASTER_DB.exists():
        raise FileNotFoundError(MASTER_DB)
    if not APPS_DB.exists():
        raise FileNotFoundError(APPS_DB)

    print(f"Master DB:      {MASTER_DB}")
    print(f"Applications:   {APPS_DB}")
    print(f"Threshold:      {args.threshold} distinct users")
    print(f"Mode:           {'DRY-RUN' if args.dry_run else 'LIVE'}")
    print()

    # ---------- Step 1: read reports ----------
    apps_con = duckdb.connect(str(APPS_DB), read_only=True)

    # job_id in applications DB has no portal prefix. fact_jobs has
    # "portal:job_id". So we suffix-match on ":<job_id>".
    reports = apps_con.execute(
        """
        SELECT
            job_id,
            COUNT(DISTINCT user_id) AS dead_reporters
        FROM applications
        WHERE reported_dead_at IS NOT NULL
        GROUP BY job_id
        HAVING COUNT(DISTINCT user_id) >= ?
        """,
        [args.threshold],
    ).fetchall()

    apps_con.close()

    print(f"Jobs over threshold: {len(reports)}")
    if reports:
        for jid, cnt in reports[:5]:
            print(f"  - {jid}  ({cnt} reporters)")
        if len(reports) > 5:
            print(f"  ... and {len(reports) - 5} more")
    print()

    if not reports:
        print("Nothing to apply.")
        return 0

    if args.dry_run:
        print("DRY-RUN: no changes written.")
        return 0

    # ---------- Step 2: flip is_active in Master DB ----------
    master_con = duckdb.connect(str(MASTER_DB))

    master_con.execute("BEGIN TRANSACTION")

    try:
        updated = 0
        for job_id_raw, count in reports:
            # Match by suffix ":<job_id>" to support portal-prefixed IDs
            pattern = f"%:{job_id_raw}"

            result = master_con.execute(
                """
                UPDATE fact_jobs
                SET is_active = FALSE,
                    reported_dead_count = ?
                WHERE job_id LIKE ?
                  AND (is_active IS NOT FALSE OR reported_dead_count < ?)
                """,
                [count, pattern, count],
            )

            # DuckDB doesn't return rowcount easily; count separately
            matched = master_con.execute(
                "SELECT COUNT(*) FROM fact_jobs WHERE job_id LIKE ?",
                [pattern],
            ).fetchone()[0]
            updated += matched

        master_con.execute("COMMIT")
        print(f"Rows affected (approx): {updated}")
        print("✓ Applied.")

    except Exception:
        master_con.execute("ROLLBACK")
        raise

    finally:
        master_con.execute("CHECKPOINT")
        master_con.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
