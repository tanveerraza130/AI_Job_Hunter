#!/usr/bin/env python3
"""
AI Job Hunter — Local Data Pipeline

Flow:
    Fetch jobs
        ↓
    Master DuckDB
        ↓
    30-day Production snapshot
        ↓
    Minimal GitHub snapshot
        ↓
    Validation

This script publishes the production snapshot to S3 and GitHub.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MAIN_SCRIPT = ROOT / "main.py"
BUILD_SCRIPT = ROOT / "scripts" / "build_production_snapshot.py"
PUBLISH_SCRIPT = ROOT / "scripts" / "publish_production.py"


def run_step(name: str, command: list[str]) -> None:
    """Run one pipeline step and stop immediately on failure."""
    print()
    print("=" * 70)
    print(name)
    print("=" * 70)
    print("Command:", " ".join(command))
    print("-" * 70)

    started_at = time.monotonic()

    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
        )
    except Exception as exc:
        elapsed = time.monotonic() - started_at
        print()
        print("=" * 70)
        print("❌ PIPELINE STEP FAILED")
        print("=" * 70)
        print(f"Failed step : {name}")
        print(f"Elapsed     : {elapsed:.1f}s")
        print(f"Exception   : {type(exc).__name__}: {exc}")
        print(f"Command     : {' '.join(command)}")
        print("Pipeline stopped immediately.")
        print("=" * 70)
        raise

    elapsed = time.monotonic() - started_at

    if result.returncode != 0:
        print()
        print("=" * 70)
        print("❌ PIPELINE STEP FAILED")
        print("=" * 70)
        print(f"Failed step : {name}")
        print(f"Exit code   : {result.returncode}")
        print(f"Elapsed     : {elapsed:.1f}s")
        print(f"Command     : {' '.join(command)}")
        print("Pipeline stopped immediately.")
        print("=" * 70)
        raise RuntimeError(
            f"Pipeline step failed: {name} "
            f"(exit code {result.returncode})"
        )

    print("-" * 70)
    print(f"✓ {name} PASS")
    print(f"Elapsed: {elapsed:.1f}s")


def main() -> int:
    print("=" * 70)
    print("AI JOB HUNTER — LOCAL DATA PIPELINE")
    print("=" * 70)

    if not BUILD_SCRIPT.exists():
        raise FileNotFoundError(
            f"Missing build script: {BUILD_SCRIPT}"
        )

    if not PUBLISH_SCRIPT.exists():
        raise FileNotFoundError(
            f"Missing publish script: {PUBLISH_SCRIPT}"
        )

    # ------------------------------------------------------------
    # STEP 1 — FETCH → MASTER DB
    # ------------------------------------------------------------

    import argparse

    parser = argparse.ArgumentParser(
        description="Run the AI Job Hunter production pipeline."
    )
    parser.add_argument(
        "--connector",
        choices=["all", "linkedin"],
        default="all",
        help="Connector to run. Default: all (Naukri + IIMJobs + Foundit + LinkedIn).",
    )
    args = parser.parse_args()

    run_step(
        "STEP 1 — FETCH → MASTER DB",
        [
            sys.executable,
            str(MAIN_SCRIPT),
            "--profile",
            "crm_manager",
            "--connector",
            args.connector,
            "--exporter",
            "duckdb",
            "--output",
            str(ROOT / "output"),
        ],
    )

    # ------------------------------------------------------------
    # STEP 2
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    # STEP 2 — BUILD PRODUCTION + MINIMAL
    # ------------------------------------------------------------

    run_step(
        "STEP 2 — BUILD PRODUCTION + MINIMAL SNAPSHOTS",
        [
            sys.executable,
            str(BUILD_SCRIPT),
            "--master-db",
            str(ROOT / "output" / "job_hunter.duckdb"),
            "--production-db",
            str(ROOT / "output" / "job_hunter_production.duckdb"),
            "--minimal-db",
            str(ROOT / "output" / "job_hunter_production_minimal.duckdb"),
        ],
    )

    # ------------------------------------------------------------
    # STEP 3 — PUBLISH PRODUCTION
    # ------------------------------------------------------------

    run_step(
        "STEP 3 — PUBLISH TO S3 + GITHUB",
        [
            sys.executable,
            str(PUBLISH_SCRIPT),
        ],
    )

    # ------------------------------------------------------------
    # COMPLETE
    # ------------------------------------------------------------

    print()
    print("=" * 70)
    print("🚀 FULL PRODUCTION PIPELINE COMPLETE")
    print("=" * 70)

    print()
    print("Final flow:")
    print("  Fetch")
    print("      ↓")
    print("  Master DB")
    print("      ↓")
    print("  Production DB — rolling 30 days")
    print("      ↓")
    print("  Minimal DB")
    print("      ↓")
    print("  S3 Production")
    print("      ↓")
    print("  GitHub Minimal Snapshot")
    print("      ↓")
    print("  AWS automatic DB refresh")
    print("      ↓")
    print("  Live Frontend")

    print()
    print("✓ End-to-end production publish complete")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print()
        print("=" * 70)
        print("❌ FULL PIPELINE FAILED")
        print("=" * 70)
        print(f"Error: {type(exc).__name__}: {exc}")
        print("The pipeline was stopped. Debug the failed step before rerunning.")
        print("=" * 70)
        raise
