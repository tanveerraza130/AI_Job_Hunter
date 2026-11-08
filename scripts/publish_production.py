from __future__ import annotations

import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_DB = ROOT / "output" / "job_hunter_production.duckdb"
MINIMAL_DB = ROOT / "output" / "job_hunter_production_minimal.duckdb"

HOST = "root@138.252.100.140"
REMOTE_DIR = "/opt/ai-job-hunter/output"
REMOTE_DB = f"{REMOTE_DIR}/job_hunter_production_minimal.duckdb"
INCOMING = f"{REMOTE_DB}.incoming"


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    for path in (PRODUCTION_DB, MINIMAL_DB):
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Missing or empty snapshot: {path}")

    print("Validating local production snapshot...", flush=True)

    import duckdb

    with duckdb.connect(str(MINIMAL_DB), read_only=True) as db:
        required = {
            "fact_jobs", "fact_job_scores", "fact_jobs_skills",
            "dim_company", "dim_location", "dim_skill",
            "job_registry", "search_session",
        }
        tables = {row[0] for row in db.execute("SHOW TABLES").fetchall()}
        missing = required - tables
        if missing:
            raise RuntimeError(f"Missing tables: {sorted(missing)}")

        count = db.execute("SELECT COUNT(*) FROM fact_jobs").fetchone()[0]
        if count == 0:
            raise RuntimeError("Snapshot has zero jobs")

    local_hash = sha256(MINIMAL_DB)
    print(f"Local jobs: {count:,}", flush=True)
    print(f"SHA256: {local_hash}", flush=True)

    print("Creating remote incoming upload...", flush=True)
    run(["ssh", HOST, f"mkdir -p '{REMOTE_DIR}'"])
    run(["scp", str(MINIMAL_DB), f"{HOST}:{INCOMING}"])

    print("Validating and publishing on VirtualCloud...", flush=True)

    remote_script = r'''
import hashlib
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
import duckdb

incoming = Path(sys.argv[1])
target = Path(sys.argv[2])
expected = sys.argv[3]

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

if not incoming.is_file() or incoming.stat().st_size == 0:
    raise RuntimeError("Incoming database missing or empty")

if digest(incoming) != expected:
    raise RuntimeError("SHA256 mismatch; production database NOT replaced")

with duckdb.connect(str(incoming), read_only=True) as db:
    required = {
        "fact_jobs", "fact_job_scores", "fact_jobs_skills",
        "dim_company", "dim_location", "dim_skill",
        "job_registry", "search_session",
    }
    tables = {r[0] for r in db.execute("SHOW TABLES").fetchall()}
    if required - tables:
        raise RuntimeError(f"Missing tables: {sorted(required - tables)}")
    jobs = db.execute("SELECT COUNT(*) FROM fact_jobs").fetchone()[0]
    if jobs == 0:
        raise RuntimeError("Incoming snapshot has zero jobs")

backup_dir = target.parent / "publish_backups"
backup_dir.mkdir(parents=True, exist_ok=True)

if target.exists():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"job_hunter_production_minimal_{stamp}.duckdb"
    shutil.copy2(target, backup)
    print(f"BACKUP={backup}")

os.replace(incoming, target)
os.chown(target, -1, -1)
print(f"PUBLISHED={target}")
print(f"JOBS={jobs}")
print(f"SHA256={digest(target)}")
'''

    run([
        "ssh", HOST,
        f"/opt/ai-job-hunter/.venv/bin/python -c "
        f"{__import__('shlex').quote(remote_script)} "
        f"{__import__('shlex').quote(INCOMING)} "
        f"{__import__('shlex').quote(REMOTE_DB)} "
        f"{__import__('shlex').quote(local_hash)}"
    ])

    print("LIVE PUBLISH SUCCESSFUL", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"PUBLISH FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
