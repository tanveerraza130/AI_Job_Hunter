"""
Migrate the legacy application DB to per-user ownership.

Legacy schema:
    job_id PRIMARY KEY
    profile_id
    status
    applied_at
    notes
    updated_at
    created_at

New schema:
    user_id
    job_id
    profile_id
    status
    applied_at
    notes
    updated_at
    created_at

Ownership:
    UNIQUE(user_id, job_id)
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "application.duckdb"
ACCOUNT_DB_PATH = PROJECT_ROOT / "data" / "account.duckdb"

LEGACY_PROFILE_ID = "crm_manager"
LEGACY_USER_ID = "130fca59-baa8-4817-9827-c9af9817fce4"


def validate_legacy_owner() -> None:
    """Verify the selected legacy owner exists and owns the profile."""
    connection = duckdb.connect(
        str(ACCOUNT_DB_PATH),
        read_only=True,
    )

    try:
        rows = connection.execute(
            """
            SELECT user_id, profile_id
            FROM user_profiles
            WHERE profile_id = ?
            """,
            [LEGACY_PROFILE_ID],
        ).fetchall()

        if LEGACY_USER_ID not in {row[0] for row in rows}:
            raise RuntimeError(
                "Legacy user_id does not own the legacy profile."
            )

        print("Legacy owner verified:")
        print(f"  user_id:    {LEGACY_USER_ID}")
        print(f"  profile_id: {LEGACY_PROFILE_ID}")

    finally:
        connection.close()


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)

    if not ACCOUNT_DB_PATH.exists():
        raise FileNotFoundError(ACCOUNT_DB_PATH)

    connection = duckdb.connect(str(DB_PATH))

    try:
        columns = {
            row[0]
            for row in connection.execute(
                "DESCRIBE applications"
            ).fetchall()
        }

        if "user_id" in columns:
            print("Migration already applied. Nothing to do.")
            return

        validate_legacy_owner()

        legacy_rows = connection.execute(
            """
            SELECT
                job_id,
                profile_id,
                status,
                applied_at,
                notes,
                updated_at,
                created_at
            FROM applications
            ORDER BY created_at, job_id
            """
        ).fetchall()

        print(f"Legacy application rows: {len(legacy_rows)}")

        invalid_profiles = {
            row[1]
            for row in legacy_rows
            if row[1] != LEGACY_PROFILE_ID
        }

        if invalid_profiles:
            raise RuntimeError(
                "Unexpected legacy profile IDs: "
                f"{sorted(invalid_profiles)}"
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = DB_PATH.with_name(
            f"application.duckdb.pre_user_migration_{timestamp}"
        )

        shutil.copy2(DB_PATH, backup_path)

        print(f"Production backup created: {backup_path}")

        connection.execute("BEGIN TRANSACTION")

        connection.execute(
            """
            CREATE TABLE applications_v2 (
                user_id VARCHAR NOT NULL,
                job_id VARCHAR NOT NULL,
                profile_id VARCHAR NOT NULL,
                status VARCHAR NOT NULL DEFAULT 'saved',
                applied_at TIMESTAMP,
                notes VARCHAR NOT NULL DEFAULT '',
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, job_id)
            )
            """
        )

        for row in legacy_rows:
            (
                job_id,
                profile_id,
                status,
                applied_at,
                notes,
                updated_at,
                created_at,
            ) = row

            connection.execute(
                """
                INSERT INTO applications_v2 (
                    user_id,
                    job_id,
                    profile_id,
                    status,
                    applied_at,
                    notes,
                    updated_at,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    LEGACY_USER_ID,
                    job_id,
                    profile_id,
                    status,
                    applied_at,
                    notes,
                    updated_at,
                    created_at,
                ],
            )

        migrated_count = connection.execute(
            "SELECT COUNT(*) FROM applications_v2"
        ).fetchone()[0]

        if migrated_count != len(legacy_rows):
            raise RuntimeError(
                f"Migration count mismatch: "
                f"{len(legacy_rows)} → {migrated_count}"
            )

        connection.execute(
            """
            ALTER TABLE applications
            RENAME TO applications_legacy
            """
        )

        connection.execute(
            """
            ALTER TABLE applications_v2
            RENAME TO applications
            """
        )

        final_count = connection.execute(
            "SELECT COUNT(*) FROM applications"
        ).fetchone()[0]

        legacy_count = connection.execute(
            "SELECT COUNT(*) FROM applications_legacy"
        ).fetchone()[0]

        if final_count != legacy_count:
            raise RuntimeError(
                f"Final count mismatch: "
                f"legacy={legacy_count}, new={final_count}"
            )

        connection.execute("COMMIT")

        print()
        print("========================================")
        print("APPLICATION DB MIGRATION SUCCESSFUL")
        print("========================================")
        print(f"Rows migrated: {final_count}")
        print(f"Legacy rows:   {legacy_count}")
        print(f"Backup:        {backup_path}")

        print()
        print("Migrated records:")

        for row in connection.execute(
            """
            SELECT
                user_id,
                job_id,
                profile_id,
                status
            FROM applications
            ORDER BY created_at, job_id
            """
        ).fetchall():
            print(row)

    except Exception:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass

        print()
        print("MIGRATION FAILED.")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
