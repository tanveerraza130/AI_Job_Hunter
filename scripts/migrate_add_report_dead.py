#!/usr/bin/env python3
"""
One-time migration: add reported_dead_at to applications table.

Backed by data/application.duckdb.

Column:
  reported_dead_at TIMESTAMP — when THIS user reported this job as dead

Safe to re-run — checks column existence first.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "application.duckdb"


def main() -> int:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Application DB not found: {DB_PATH}")

    print(f"Target DB: {DB_PATH}")
    print()

    # Backup
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.with_suffix(f".before_report_dead_{ts}.duckdb")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup}")
    print()

    con = duckdb.connect(str(DB_PATH))

    current = {
        row[0]
        for row in con.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'applications'
            """
        ).fetchall()
    }

    print(f"applications columns before ({len(current)}):")
    for col in sorted(current):
        print(f"  - {col}")
    print()

    if "reported_dead_at" in current:
        print("SKIP reported_dead_at (already exists)")
    else:
        print("ADD reported_dead_at TIMESTAMP")
        con.execute(
            "ALTER TABLE applications ADD COLUMN reported_dead_at TIMESTAMP"
        )
        print("Column added.")
    print()

    after = {
        row[0]
        for row in con.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'applications'
            """
        ).fetchall()
    }
    print(f"applications columns after ({len(after)}):")
    for col in sorted(after):
        print(f"  - {col}")

    con.execute("CHECKPOINT")
    con.close()

    print()
    print("✓ Migration complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
