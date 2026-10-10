#!/usr/bin/env python3
"""
Daily job liveness prune.

Marks fact_jobs rows as is_active = FALSE when:
  - last_seen_at < NOW() - <THRESHOLD> days
  - AND is_active = TRUE (avoid rewriting already-inactive rows)

Never deletes rows. Application status history is preserved.
Safe to run repeatedly. Includes --dry-run mode.

Usage:
  python3 scripts/prune_stale_jobs.py              # actually prune
  python3 scripts/prune_stale_jobs.py --dry-run    # preview only
  python3 scripts/prune_stale_jobs.py --days 14    # custom threshold
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
MASTER_DB = ROOT / "output" / "job_hunter.duckdb"
DEFAULT_THRESHOLD_DAYS = 30


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview affected rows without writing",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_THRESHOLD_DAYS,
        help=f"Staleness threshold (default: {DEFAULT_THRESHOLD_DAYS})",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=str(MASTER_DB),
        help="Path to Master DB",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")

    print(f"Target DB:  {db_path}")
    print(f"Threshold:  {args.days} days")
    print(f"Mode:       {'DRY-RUN' if args.dry_run else 'LIVE'}")
    print()

    con = duckdb.connect(str(db_path), read_only=args.dry_run)

    # Sanity: row counts before
    total_before = con.execute(
        "SELECT COUNT(*) FROM fact_jobs"
    ).fetchone()[0]
    active_before = con.execute(
        "SELECT COUNT(*) FROM fact_jobs WHERE is_active IS NOT FALSE"
    ).fetchone()[0]

    print(f"Rows total:    {total_before:,}")
    print(f"Rows active:   {active_before:,}")
    print()

    # How many rows are stale?
    stale_count = con.execute(
        f"""
        SELECT COUNT(*) FROM fact_jobs
        WHERE last_seen_at IS NOT NULL
          AND last_seen_at < NOW() - INTERVAL {args.days} DAY
          AND is_active IS NOT FALSE
        """
    ).fetchone()[0]

    print(f"Stale (to deactivate): {stale_count:,}")
    print()

    if stale_count == 0:
        print("Nothing to do.")
        con.close()
        return 0

    # Sample: show 5 oldest stale job_ids
    sample = con.execute(
        f"""
        SELECT job_id, portal, last_seen_at
        FROM fact_jobs
        WHERE last_seen_at IS NOT NULL
          AND last_seen_at < NOW() - INTERVAL {args.days} DAY
          AND is_active IS NOT FALSE
        ORDER BY last_seen_at ASC
        LIMIT 5
        """
    ).fetchall()

    print("Oldest stale jobs (sample):")
    for jid, portal, last_seen in sample:
        print(f"  - {jid}  [{portal}]  last_seen={last_seen}")
    print()

    if args.dry_run:
        print("DRY-RUN: no changes written.")
        con.close()
        return 0

    # ---- LIVE write ----
    con.execute("BEGIN TRANSACTION")

    try:
        con.execute(
            f"""
            UPDATE fact_jobs
            SET is_active = FALSE
            WHERE last_seen_at IS NOT NULL
              AND last_seen_at < NOW() - INTERVAL {args.days} DAY
              AND is_active IS NOT FALSE
            """
        )

        active_after = con.execute(
            "SELECT COUNT(*) FROM fact_jobs WHERE is_active IS NOT FALSE"
        ).fetchone()[0]

        con.execute("COMMIT")

        print(f"Rows active after:  {active_after:,}")
        print(f"Rows deactivated:   {active_before - active_after:,}")
        print()

        con.execute("CHECKPOINT")
        print("✓ Prune complete.")

    except Exception:
        con.execute("ROLLBACK")
        raise

    finally:
        con.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
