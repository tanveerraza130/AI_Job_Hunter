#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PRODUCTION_DB = ROOT / "output" / "job_hunter_production.duckdb"
MINIMAL_DB = ROOT / "output" / "job_hunter_production_minimal.duckdb"

BUCKET = "s3://ai-job-hunter-production-db"
PRODUCTION_KEY = f"{BUCKET}/job_hunter.duckdb"
BACKUP_PREFIX = f"{BUCKET}/backups"
RELEASE_PREFIX = f"{BUCKET}/releases"


def run(name: str, command: list[str]) -> str:
    print()
    print("=" * 70)
    print(name)
    print("=" * 70)
    print("$", " ".join(command))

    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    if result.stdout:
        print(result.stdout, end="")

    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        raise RuntimeError(f"{name} FAILED")

    print(f"✓ {name} PASS")
    return result.stdout


def main() -> int:
    print("=" * 70)
    print("AI JOB HUNTER — AUTOMATIC PRODUCTION PUBLISH")
    print("=" * 70)

    if not PRODUCTION_DB.exists():
        raise FileNotFoundError(PRODUCTION_DB)

    if not MINIMAL_DB.exists():
        raise FileNotFoundError(MINIMAL_DB)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    backup_key = f"{BACKUP_PREFIX}/job_hunter_{timestamp}.duckdb"
    release_key = f"{RELEASE_PREFIX}/job_hunter_{timestamp}.duckdb"

    # ------------------------------------------------------------
    # 1. BACKUP CURRENT LIVE DB
    # ------------------------------------------------------------

    run(
        "BACKUP CURRENT S3 PRODUCTION DB",
        [
            "aws",
            "s3",
            "cp",
            PRODUCTION_KEY,
            backup_key,
        ],
    )

    # ------------------------------------------------------------
    # 2. UPLOAD CANDIDATE RELEASE
    # ------------------------------------------------------------

    run(
        "UPLOAD PRODUCTION CANDIDATE",
        [
            "aws",
            "s3",
            "cp",
            str(PRODUCTION_DB),
            release_key,
        ],
    )

    # ------------------------------------------------------------
    # 3. VERIFY CANDIDATE
    # ------------------------------------------------------------

    run(
        "VERIFY S3 CANDIDATE",
        [
            "aws",
            "s3",
            "ls",
            release_key,
        ],
    )

    # ------------------------------------------------------------
    # 4. PROMOTE CANDIDATE TO LIVE
    # ------------------------------------------------------------

    run(
        "PROMOTE PRODUCTION DB",
        [
            "aws",
            "s3",
            "cp",
            release_key,
            PRODUCTION_KEY,
        ],
    )

    # ------------------------------------------------------------
    # 5. VERIFY LIVE S3 DB
    # ------------------------------------------------------------

    run(
        "VERIFY LIVE S3 PRODUCTION DB",
        [
            "aws",
            "s3",
            "ls",
            PRODUCTION_KEY,
        ],
    )

    # ------------------------------------------------------------
    # 6. PUBLISH MINIMAL SNAPSHOT TO GITHUB
    # ------------------------------------------------------------

    run(
        "STAGE MINIMAL GITHUB SNAPSHOT",
        [
            "git",
            "add",
            "-f",
            str(MINIMAL_DB.relative_to(ROOT)),
        ],
    )

    staged = subprocess.run(
        [
            "git",
            "diff",
            "--cached",
            "--name-only",
            "--",
            str(MINIMAL_DB.relative_to(ROOT)),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    staged_files = [
        line.strip()
        for line in staged.stdout.splitlines()
        if line.strip()
    ]

    print("Staged minimal snapshot:")
    if staged_files:
        for file in staged_files:
            print(f"  {file}")
    else:
        print("  (none)")

    if not staged_files:
        print("✓ GitHub snapshot already current")
    else:
        run(
            "COMMIT MINIMAL SNAPSHOT",
            [
                "git",
                "commit",
                "--only",
                "-m",
                f"Update production snapshot {timestamp}",
                "--",
                str(MINIMAL_DB.relative_to(ROOT)),
            ],
        )

        run(
            "PUSH MINIMAL SNAPSHOT TO GITHUB",
            [
                "git",
                "push",
                "origin",
                "HEAD",
            ],
        )

    print()
    print("=" * 70)
    print("🚀 PRODUCTION PUBLISH COMPLETE")
    print("=" * 70)
    print(f"Production DB : {PRODUCTION_DB}")
    print(f"S3 production : {PRODUCTION_KEY}")
    print(f"S3 backup     : {backup_key}")
    print(f"S3 release    : {release_key}")
    print(f"GitHub        : {MINIMAL_DB.name}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
