"""
Integration tests for Job Registry.

These tests verify the registry business logic works correctly.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta

import duckdb
import pytest

from jobs.job import Job
from jobs.registry import JobRegistry, JobRegistryRepository, JobStatus


class TestJobRegistry:
    """Test suite for JobRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a registry instance with schema applied."""
        conn = duckdb.connect(":memory:")

        # Resolve schema path relative to this test file
        # Project structure:
        #   AI_Job_Hunter/
        #   └── jobs/
        #       ├── storage/
        #       │   └── schema.sql
        #       └── tests/
        #           └── integration/
        #               └── test_job_registry.py
        #
        # Path(__file__).resolve() = .../AI_Job_Hunter/jobs/tests/integration/test_job_registry.py
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

        repo = JobRegistryRepository(conn)
        return JobRegistry(repo)

    def test_save_and_exists(self, registry):
        """Test that save creates a record and exists returns True."""
        job = Job(
            job_id="test123",
            title="Test Job",
            company="Test Corp",
            location="Remote",
            description="Test description for save_and_exists",
            job_url="https://example.com/job/test123",
            portal="test",
        )

        assert registry.exists(job) is False

        registry.save(job)
        assert registry.exists(job) is True

        registry.save(job)
        assert registry.exists(job) is True

    def test_save_without_job_id_uses_fallback(self, registry):
        """Test that save works without portal_job_id using fallback fields."""
        job = Job(
            job_id="",
            title="Test Job",
            company="Test Corp",
            location="Remote",
            description="Test description for fallback",
            job_url="https://example.com/job/fallback",
            portal="test",
        )

        registry.save(job)
        assert registry.exists(job) is True

    def test_mark_seen_transition(self, registry):
        """Test that mark_seen transitions NEW to SEEN or updates timestamp."""
        job = Job(
            job_id="test456",
            title="Test Job 2",
            company="Test Corp",
            location="Remote",
            description="Test description for mark_seen",
            job_url="https://example.com/job/test456",
            portal="test",
        )

        registry.save(job)
        assert registry.get_status(job) == JobStatus.NEW

        registry.mark_seen(job)
        assert registry.get_status(job) == JobStatus.SEEN

        registry.mark_seen(job)
        assert registry.get_status(job) == JobStatus.SEEN

    def test_lifecycle_transitions(self, registry):
        """Test the full job lifecycle transitions."""
        job = Job(
            job_id="test789",
            title="Test Job 3",
            company="Test Corp",
            location="Remote",
            description="Test description for lifecycle",
            job_url="https://example.com/job/test789",
            portal="test",
        )

        registry.save(job)
        assert registry.get_status(job) == JobStatus.NEW

        registry.mark_applied(job)
        assert registry.get_status(job) == JobStatus.APPLIED

        registry.mark_applied(job)
        assert registry.get_status(job) == JobStatus.APPLIED

    def test_mark_rejected(self, registry):
        """Test that mark_rejected transitions to REJECTED."""
        job = Job(
            job_id="test_reject",
            title="Test Job",
            company="Test Corp",
            location="Remote",
            description="Test description for rejected",
            job_url="https://example.com/job/test_reject",
            portal="test",
        )

        registry.save(job)
        assert registry.get_status(job) == JobStatus.NEW

        registry.mark_rejected(job, reason="Not a match")
        assert registry.get_status(job) == JobStatus.REJECTED

        registry.mark_seen(job)
        assert registry.get_status(job) == JobStatus.REJECTED

    def test_mark_expired(self, registry):
        """Test that mark_expired transitions to EXPIRED and prevents further transitions."""
        job = Job(
            job_id="test_expire",
            title="Test Job",
            company="Test Corp",
            location="Remote",
            description="Test description for expired",
            job_url="https://example.com/job/test_expire",
            portal="test",
        )

        registry.save(job)
        assert registry.get_status(job) == JobStatus.NEW

        registry.mark_expired(job)
        assert registry.get_status(job) == JobStatus.EXPIRED

        # EXPIRED is terminal, so mark_applied should raise
        with pytest.raises(RuntimeError) as excinfo:
            registry.mark_applied(job)

        assert "Invalid transition" in str(excinfo.value)
        assert registry.get_status(job) == JobStatus.EXPIRED

    def test_invalid_transition_raises(self, registry):
        """Test that invalid transitions raise RuntimeError."""
        job = Job(
            job_id="test_invalid",
            title="Test Job",
            company="Test Corp",
            location="Remote",
            description="Test description for invalid transition",
            job_url="https://example.com/job/test_invalid",
            portal="test",
        )

        registry.save(job)

        registry.mark_applied(job)
        assert registry.get_status(job) == JobStatus.APPLIED

        with pytest.raises(RuntimeError) as excinfo:
            registry.mark_rejected(job)

        assert "Invalid transition" in str(excinfo.value)

    def test_get_new_jobs(self, registry):
        """Test that get_new_jobs returns only NEW jobs."""
        job1 = Job(
            job_id="new1",
            title="New Job 1",
            company="Test",
            location="Remote",
            description="Test description for job1",
            job_url="https://example.com/job/new1",
            portal="test",
        )
        job2 = Job(
            job_id="new2",
            title="New Job 2",
            company="Test",
            location="Remote",
            description="Test description for job2",
            job_url="https://example.com/job/new2",
            portal="test",
        )
        job3 = Job(
            job_id="seen1",
            title="Seen Job",
            company="Test",
            location="Remote",
            description="Test description for job3",
            job_url="https://example.com/job/seen1",
            portal="test",
        )

        registry.save(job1)
        registry.save(job2)
        registry.save(job3)

        registry.mark_seen(job3)

        new_jobs = registry.get_new_jobs()
        fingerprints = [j.fingerprint for j in new_jobs]

        assert len(new_jobs) == 2
        assert registry._get_fingerprint(job1) in fingerprints
        assert registry._get_fingerprint(job2) in fingerprints
        assert registry._get_fingerprint(job3) not in fingerprints

    def test_get_status_returns_none_for_unknown(self, registry):
        """Test that get_status returns None for unknown jobs."""
        job = Job(
            job_id="unknown",
            title="Unknown Job",
            company="Test",
            location="Remote",
            description="Test description for unknown",
            job_url="https://example.com/job/unknown",
            portal="test",
        )

        status = registry.get_status(job)
        assert status is None

    def test_expire_old_jobs_batch(self, registry):
        """Test that expire_old_jobs batch expiration works."""
        job = Job(
            job_id="batch_expire",
            title="Batch Expire Job",
            company="Test",
            location="Remote",
            description="Test description for batch expire",
            job_url="https://example.com/job/batch_expire",
            portal="test",
        )

        registry.save(job)

        fingerprint = registry._get_fingerprint(job)
        old_time = datetime.now() - timedelta(days=60)
        registry.repo.connection.execute(
            """
            UPDATE job_registry
            SET last_seen_at = ?
            WHERE fingerprint = ?
            """,
            [old_time, fingerprint],
        )

        expired_count = registry.expire_old_jobs(older_than_days=30)
        assert expired_count == 1

        status = registry.get_status(job)
        assert status == JobStatus.EXPIRED


# =============================================================================
# END OF FILE
# =============================================================================