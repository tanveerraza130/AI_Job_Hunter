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

    import argparse

    parser = argparse.ArgumentParser(
        description="Run the AI Job Hunter production pipeline."
    )
    parser.add_argument(
        "--connector",
        choices=[
            "all",
            "naukri",
            "iimjobs",
            "foundit",
            "linkedin",
            "greenhouse",
        ],
        default="all",
        help=(
            "Connector to run. Default: all "
            "(Naukri + IIMJobs + Foundit + LinkedIn + Greenhouse)."
        ),
    )
    args = parser.parse_args()

    if args.connector == "all":
        connector_names = [
            "naukri",
            "iimjobs",
            "foundit",
            "linkedin",
            "greenhouse",
        ]
    else:
        connector_names = [args.connector]

    for connector_name in connector_names:
        print()
        print("=" * 70)
        print(
            f"🚀 STARTING CONNECTOR: "
            f"{connector_name.upper()}"
        )
        print("=" * 70)

        # --------------------------------------------------------
        # STEP 1 — FETCH → MASTER DB
        # --------------------------------------------------------

        run_step(
            f"{connector_name.upper()} — FETCH → MASTER DB",
            [
                sys.executable,
                str(MAIN_SCRIPT),
                "--profile",
                "crm_manager",
                "--connector",
                connector_name,
                "--exporter",
                "duckdb",
                "--output",
                str(ROOT / "output"),
            ],
        )

        # --------------------------------------------------------
        # STEP 2 — BUILD PRODUCTION + MINIMAL
        # --------------------------------------------------------

        run_step(
            f"{connector_name.upper()} — BUILD PRODUCTION + MINIMAL",
            [
                sys.executable,
                str(BUILD_SCRIPT),
                "--master-db",
                str(ROOT / "output" / "job_hunter.duckdb"),
                "--production-db",
                str(ROOT / "output" / "job_hunter_production.duckdb"),
                "--minimal-db",
                str(
                    ROOT
                    / "output"
                    / "job_hunter_production_minimal.duckdb"
                ),
            ],
        )

        # --------------------------------------------------------
        # STEP 3 — PUBLISH → AWS + GITHUB
        # --------------------------------------------------------

        run_step(
            f"{connector_name.upper()} — PUBLISH → AWS + GITHUB",
            [
                sys.executable,
                str(PUBLISH_SCRIPT),
            ],
        )

        print()
        print("=" * 70)
        print(
            f"✓ {connector_name.upper()} COMPLETE AND LIVE"
        )
        print(
            "Starting next connector..."
        )
        print("=" * 70)

    print()
    print("=" * 70)
    print("🚀 FULL PRODUCTION PIPELINE COMPLETE")
    print("=" * 70)

    print()
    print("Final flow:")
    print(
        "  Naukri → FETCH → MASTER → BUILD → AWS/GitHub → LIVE"
    )
    print(
        "  IIMJobs → FETCH → MASTER → BUILD → AWS/GitHub → LIVE"
    )
    print(
        "  Foundit → FETCH → MASTER → BUILD → AWS/GitHub → LIVE"
    )
    print(
        "  LinkedIn → FETCH → MASTER → BUILD → AWS/GitHub → LIVE"
    )
    print(
        "  Greenhouse → FETCH → MASTER → BUILD → AWS/GitHub → LIVE"
    )

    print()
    print("✓ End-to-end connector-by-connector production publish complete")

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
