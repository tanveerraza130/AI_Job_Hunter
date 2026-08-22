"""
Integration tests for Job Registry Repository.

These tests verify the repository layer works with the target DuckDB version.
Tests focus on public contract, not implementation details.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import duckdb
import pytest

from jobs.registry.models import JobStatus
from jobs.storage.job_registry_repository import JobRegistryRepository


class TestJobRegistryRepository:
    """Test suite for JobRegistryRepository."""

    @pytest.fixture
    def conn(self):
        """Create an in-memory DuckDB connection with schema applied."""
        conn = duckdb.connect(":memory:")

        # Resolve schema path relative to this test file
        # Project structure:
        #   AI_Job_Hunter/
        #   └── jobs/
        #       ├── storage/
        #       │   └── schema.sql
        #       └── tests/
        #           └── integration/
        #               └── test_job_registry_repository.py
        #
        # Path(__file__).resolve() = .../AI_Job_Hunter/jobs/tests/integration/test_job_registry_repository.py
        # parents[0] = .../AI_Job_Hunter/jobs/tests/integration
        # parents[1] = .../AI_Job_Hunter/jobs/tests
        # parents[2] = .../AI_Job_Hunter/jobs
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "storage"
            / "schema.sql"
        )

        schema_sql = schema_path.read_text(encoding="utf-8")
        conn.execute(schema_sql)

        yield conn
        conn.close()

    @pytest.fixture
    def repo(self, conn):
        """Create a repository instance."""
        return JobRegistryRepository(conn)

    def test_insert_or_ignore_contract(self, repo):
        """Test that insert_or_ignore returns True on insert, False on duplicate."""
        result1 = repo.insert_or_ignore(
            fingerprint="fp1",
            portal="test",
            portal_job_id="job1",
            company="Test Corp",
            title="Test Job",
            location="Remote",
            status=JobStatus.NEW.value,
        )
        assert result1 is True, "First insert should return True"

        result2 = repo.insert_or_ignore(
            fingerprint="fp1",
            portal="test",
            portal_job_id="job2",
            company="Test Corp 2",
            title="Test Job 2",
            location="Remote",
            status=JobStatus.NEW.value,
        )
        assert result2 is False, "Duplicate insert should return False"

        results = repo.get_by_status(JobStatus.NEW)
        assert len(results) == 1, "Only one record should exist"

    def test_metadata_merge(self, repo):
        """Test that metadata is correctly merged using json_merge_patch."""
        repo.insert_or_ignore(
            fingerprint="fp2",
            portal="test",
            portal_job_id="job3",
            company="Test Corp",
            title="Test Job",
            location="Remote",
            status=JobStatus.NEW.value,
            metadata={"source": "cron", "user": "admin"},
        )

        repo.update_status(
            fingerprint="fp2",
            status=JobStatus.APPLIED.value,
            timestamp_column="applied_at",
            metadata={"source": "scheduler"},
        )

        record = repo.get("fp2")
        assert record is not None
        assert record.metadata is not None
        assert record.metadata.get("source") == "scheduler"
        assert record.metadata.get("user") == "admin"

    def test_partial_index_contract(self, repo):
        """Test that the partial unique index prevents duplicates with same portal_job_id."""
        repo.insert_or_ignore(
            fingerprint="fp3",
            portal="test",
            portal_job_id="unique_job",
            company="Test Corp",
            title="Test Job",
            location="Remote",
            status=JobStatus.NEW.value,
        )

        result = repo.insert_or_ignore(
            fingerprint="fp4",
            portal="test",
            portal_job_id="unique_job",
            company="Test Corp 2",
            title="Test Job 2",
            location="Remote",
            status=JobStatus.NEW.value,
        )
        assert result is False, "Duplicate insert should return False"

        repo.insert_or_ignore(
            fingerprint="fp5",
            portal="test",
            portal_job_id="",
            company="Test Corp 3",
            title="Test Job 3",
            location="Remote",
            status=JobStatus.NEW.value,
        )

        repo.insert_or_ignore(
            fingerprint="fp6",
            portal="test",
            portal_job_id="",
            company="Test Corp 4",
            title="Test Job 4",
            location="Remote",
            status=JobStatus.NEW.value,
        )

        results = repo.get_by_status(JobStatus.NEW)
        assert len(results) == 3, "Should have 3 records"

    def test_expire_old_jobs(self, repo):
        """Test that expire_old_jobs correctly marks old jobs as expired."""
        fingerprint = "fp_expire"
        now = datetime.now()

        repo.insert_or_ignore(
            fingerprint=fingerprint,
            portal="test",
            portal_job_id="expire_job",
            company="Test Corp",
            title="Test Job",
            location="Remote",
            status=JobStatus.NEW.value,
        )

        cutoff = now - timedelta(days=60)
        repo.connection.execute(
            """
            UPDATE job_registry
            SET last_seen_at = ?
            WHERE fingerprint = ?
            """,
            [cutoff, fingerprint],
        )

        expired_count = repo.expire_old_jobs(older_than_days=30)
        assert expired_count == 1, "Should expire exactly one job"

        record = repo.get(fingerprint)
        assert record is not None
        assert record.status == JobStatus.EXPIRED, "Job should be EXPIRED"

    def test_update_status_invalid_timestamp_column(self, repo):
        """Test that invalid timestamp column raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            repo.update_status(
                fingerprint="fp_invalid",
                status=JobStatus.APPLIED.value,
                timestamp_column="invalid_column",
            )
        assert "Invalid timestamp column" in str(excinfo.value)

    def test_get_by_status_returns_correct_records(self, repo):
        """Test that get_by_status returns only records with the specified status."""
        repo.insert_or_ignore(
            fingerprint="fp_status1",
            portal="test",
            portal_job_id="status1",
            company="Test Corp",
            title="Test Job 1",
            location="Remote",
            status=JobStatus.NEW.value,
        )

        repo.insert_or_ignore(
            fingerprint="fp_status2",
            portal="test",
            portal_job_id="status2",
            company="Test Corp",
            title="Test Job 2",
            location="Remote",
            status=JobStatus.SEEN.value,
        )

        repo.insert_or_ignore(
            fingerprint="fp_status3",
            portal="test",
            portal_job_id="status3",
            company="Test Corp",
            title="Test Job 3",
            location="Remote",
            status=JobStatus.NEW.value,
        )

        new_jobs = repo.get_by_status(JobStatus.NEW)
        assert len(new_jobs) == 2, "Should have 2 NEW jobs"

        seen_jobs = repo.get_by_status(JobStatus.SEEN)
        assert len(seen_jobs) == 1, "Should have 1 SEEN job"

        new_fingerprints = {j.fingerprint for j in new_jobs}
        assert "fp_status1" in new_fingerprints
        assert "fp_status3" in new_fingerprints
        assert "fp_status2" not in new_fingerprints

    def test_mark_seen_many_protects_terminal_states(self, repo):
        """Test that mark_seen_many only updates NEW jobs, not terminal states."""
        # Create two jobs: one NEW, one APPLIED
        repo.insert_or_ignore(
            fingerprint="fp_seen1",
            portal="test",
            portal_job_id="seen_job1",
            company="Test Corp",
            title="Test Job 1",
            location="Remote",
            status=JobStatus.NEW.value,
        )

        repo.insert_or_ignore(
            fingerprint="fp_seen2",
            portal="test",
            portal_job_id="seen_job2",
            company="Test Corp",
            title="Test Job 2",
            location="Remote",
            status=JobStatus.APPLIED.value,
        )

        # Mark both as SEEN
        repo.mark_seen_many(["fp_seen1", "fp_seen2"])

        # Verify NEW job became SEEN with updated last_seen_at
        record1 = repo.get("fp_seen1")
        assert record1 is not None
        assert record1.status == JobStatus.SEEN, "NEW job should transition to SEEN"
        assert record1.last_seen_at is not None, "last_seen_at should be updated"

        # Verify APPLIED job remained APPLIED (protected)
        record2 = repo.get("fp_seen2")
        assert record2 is not None
        assert record2.status == JobStatus.APPLIED, "APPLIED job should remain APPLIED (terminal state protected)"


# =============================================================================
# END OF FILE
# =============================================================================