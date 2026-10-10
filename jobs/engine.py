"""
File:
    engine.py

Version:
    8.1.0

Phase:
    7

Status:
    ACTIVE

Purpose:
    Main orchestration engine for AI Job Hunter.

Responsibilities:
    - execute(): Execute one search request, return raw jobs
    - run(): Execute one or more search requests
    - Identify NEW vs previously seen jobs
    - Validate NEW jobs
    - Profile-filter NEW jobs
    - Extract intelligence for NEW jobs
    - Score NEW jobs
    - Export NEW jobs
    - Track search sessions

Important incremental-storage rule:
    Existing jobs are never re-scored or re-exported.

    Pipeline:

        Fetch
          ↓
        Registry
          ↓
        NEW jobs ──→ validate → filter → score → export
          ↓
        SEEN jobs ──→ mark_seen only

Dependencies:
    - jobs.base
    - jobs.enums
    - jobs.exporter.base
    - jobs.filtering
    - jobs.identity.deduplicator
    - jobs.intelligence
    - jobs.job
    - jobs.registry
    - jobs.scoring
    - jobs.search
    - jobs.storage
    - jobs.validators

PEP8: Yes
"""

from __future__ import annotations

import logging
import platform
import time
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import duckdb
from jobs.utils.search_cache import SearchCache

from jobs.base import BaseConnector
from jobs.enums import (
    ConnectorType,
    Destination,
    ExportFormat,
    FinishedReason,
    Portal,
    SearchStatus,
    SearchType,
)
from jobs.exporter.base import BaseExporter
from jobs.filtering import ProfileJobFilter
from jobs.identity.deduplicator import JobDeduplicator
from jobs.intelligence import IntelligenceExtractor
from jobs.job import Job
from jobs.registry import JobRegistry
from jobs.scoring import ProfileScoringEngine
from jobs.search import SearchRequest
from jobs.storage.job_registry_repository import JobRegistryRepository
from jobs.storage.raw_repository import RawRepository
from jobs.storage.score_repository import ScoreRepository
from jobs.storage.session_repository import SessionRepository
from jobs.validators import JobValidator
from jobs.version import AI_PIPELINE_VERSION


logger = logging.getLogger(__name__)


@dataclass
class ExecutionSummary:
    """
    Summary of an engine execution run.

    Attributes:
        execution_id:
            UUID of the search session.

        connectors_used:
            Connectors executed during the run.

        total_jobs:
            Total jobs collected from connectors before registry processing.

        duplicate_jobs_removed:
            Number of duplicate jobs removed by the in-memory deduplicator.

        valid_jobs:
            Number of NEW jobs that passed validation/filtering.

        invalid_jobs:
            Number of NEW jobs that failed validation.

        exported_jobs:
            Number of NEW jobs successfully exported.

        destination:
            Destination path.

        errors:
            Errors encountered during execution.
    """

    execution_id: UUID
    connectors_used: list[str]
    total_jobs: int
    duplicate_jobs_removed: int
    valid_jobs: int
    invalid_jobs: int
    exported_jobs: int
    destination: Path
    errors: list[str]


class Engine:
    """
    Main orchestration engine for AI Job Hunter.

    Incremental processing contract:

        connector.fetch_jobs()
                ↓
        registry.exists()
                ↓
        ┌───────────────┐
        │               │
       NEW             SEEN
        │               │
        ↓               ↓
      process       mark_seen
        │
        ↓
      export

    Existing jobs are intentionally excluded from scoring.
    """

    def __init__(
        self,
        connectors: list[BaseConnector],
        exporter: BaseExporter,
        db_path: Path,
        destination: Destination = Destination.LOCAL,
    ) -> None:
        """
        Initialize the engine.

        Args:
            connectors:
                Configured job connectors.

            exporter:
                Output exporter.

            db_path:
                DuckDB database path.

            destination:
                Destination type.
        """
        self._connectors: list[BaseConnector] = connectors
        self._exporter: BaseExporter = exporter
        self._db_path: Path = db_path
        self._destination: Destination = destination

        self._deduplicator: JobDeduplicator = JobDeduplicator()
        self._validator: JobValidator = JobValidator()

        self._connection: duckdb.DuckDBPyConnection | None = None

        self._session_repo: SessionRepository | None = None
        self._raw_repo: RawRepository | None = None
        self._registry_repo: JobRegistryRepository | None = None
        self._registry: JobRegistry | None = None
        self._score_repo: ScoreRepository | None = None

        self._extractors: dict[str, IntelligenceExtractor] = {}
        self._scoring_engines: dict[str, ProfileScoringEngine] = {}
        self._profile_filters: dict[str, ProfileJobFilter] = {}

    # ------------------------------------------------------------------
    # Repository initialization
    # ------------------------------------------------------------------

    def _ensure_repositories(self) -> None:
        """
        Ensure database connection and repositories are initialized.
        """
        if self._connection is not None:
            return

        self._db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._connection = duckdb.connect(
            str(self._db_path)
        )

        schema_path = (
            Path(__file__).parent
            / "storage"
            / "schema.sql"
        )

        if schema_path.exists():
            schema_sql = schema_path.read_text(
                encoding="utf-8"
            )

            self._connection.execute(schema_sql)

            logger.info(
                "Database schema applied from %s",
                schema_path,
            )
        else:
            logger.warning(
                "Schema file not found: %s",
                schema_path,
            )

        self._session_repo = SessionRepository(
            self._connection
        )

        self._raw_repo = RawRepository(
            self._connection
        )

        self._registry_repo = JobRegistryRepository(
            self._connection
        )

        self._registry = JobRegistry(
            self._registry_repo
        )

        self._score_repo = ScoreRepository(
            self._connection
        )

    # ------------------------------------------------------------------
    # Scoring initialization
    # ------------------------------------------------------------------

    def _ensure_scoring_components(
        self,
        profile_type: str,
        profile,
    ) -> None:
        """
        Ensure profile-specific intelligence and scoring components.
        """
        logger.info(
            "Ensuring scoring components for profile: %s",
            profile_type,
        )

        if profile_type not in self._extractors:
            self._extractors[profile_type] = (
                IntelligenceExtractor(profile_type)
            )

        if profile_type not in self._scoring_engines:
            self._scoring_engines[profile_type] = (
                ProfileScoringEngine(profile_type)
            )

        if (
            profile_type not in self._profile_filters
            and profile is not None
        ):
            self._profile_filters[profile_type] = (
                ProfileJobFilter(profile)
            )

    # ------------------------------------------------------------------
    # Connector context
    # ------------------------------------------------------------------

    def _set_connector_context(
        self,
        connector: BaseConnector,
        session_id: UUID,
        profile_type: str | None = None,
    ) -> None:
        """
        Set repository context on connectors that support it.
        """
        if hasattr(connector, "set_repositories"):
            connector.set_repositories(
                self._raw_repo,
                session_id,
            )

        if hasattr(connector, "set_registry"):
            connector.set_registry(self._registry)

        if hasattr(connector, "set_candidate_gate"):
            connector.set_candidate_gate(
                lambda portal, portal_job_ids: self._filter_connector_candidates(
                    portal=portal,
                    portal_job_ids=portal_job_ids,
                    profile_type=profile_type,
                )
            )

    # ------------------------------------------------------------------
    # Registry
    # ------------------------------------------------------------------

    def _canonical_job_id(self, job: Job) -> str:
        """Return the canonical globally unique job ID."""
        if job.portal and ":" not in str(job.job_id):
            return f"{job.portal}:{job.job_id}"

        return str(job.job_id)

    def _save_to_registry(
        self,
        job: Job,
    ) -> None:
        """
        Save a job to registry.

        This helper is retained for compatibility.
        """
        if self._registry is None:
            logger.warning(
                "Registry not initialized; "
                "skipping job registration."
            )
            return

        try:
            self._registry.save(job)

        except Exception as exc:
            logger.warning(
                "Failed to save job to registry: %s",
                exc,
            )

    def _filter_connector_candidates(
        self,
        portal: str,
        portal_job_ids: list[str],
        profile_type: str | None = None,
    ) -> set[str]:
        """Return source job IDs that still require detail processing."""
        if not portal_job_ids:
            return set()

        if self._registry is None:
            return set(portal_job_ids)

        if not profile_type or self._score_repo is None:
            return set(portal_job_ids)

        existing_ids = self._registry.get_existing_portal_job_ids(
            portal=portal,
            portal_job_ids=portal_job_ids,
        )

        if not existing_ids:
            return set(portal_job_ids)

        canonical_ids = {
            f"{portal}:{job_id}"
            for job_id in existing_ids
        }

        scored_ids = self._score_repo.get_scored_job_ids(
            job_ids=canonical_ids,
            profile_id=profile_type,
        )

        if not scored_ids:
            return set(portal_job_ids)

        fact_job_ids = self._score_repo.get_existing_fact_job_ids(
            job_ids=scored_ids,
        )

        reusable_ids = {
            job_id.split(":", 1)[1]
            for job_id in fact_job_ids
            if job_id.startswith(f"{portal}:")
        }

        return {
            job_id
            for job_id in portal_job_ids
            if job_id not in reusable_ids
        }

    def _classify_registry_jobs(
        self,
        jobs: list[Job],
        profile_type: str | None = None,
    ) -> tuple[list[Job], int]:
        """
        Classify fetched jobs into NEW and SEEN.

        NEW jobs:
            Jobs that do not already exist in the registry.

        SEEN jobs:
            Jobs already present in the registry.

        Returns:
            Tuple of:
                - new jobs
                - number of previously-seen jobs
        """
        if self._registry is None:
            logger.warning(
                "Registry unavailable; "
                "treating all jobs as NEW."
            )

            return jobs, 0

        new_jobs: list[Job] = []
        seen_count = 0

        for job in jobs:
            try:
                if not self._registry.exists(job):
                    self._registry.save(job)
                    new_jobs.append(job)

                elif (
                    profile_type
                    and self._score_repo is not None
                ):
                    canonical_job_id = self._canonical_job_id(job)

                    if not self._score_repo.has_score(
                        job_id=canonical_job_id,
                        profile_id=profile_type,
                    ):
                        # Job exists globally, but this profile has
                        # not processed it yet. Allow profile-specific
                        # processing.
                        new_jobs.append(job)

                    else:
                        # A registry entry + profile score does not guarantee
                        # that the job was successfully persisted to fact_jobs.
                        # If scoring committed but export did not complete,
                        # the job becomes an orphaned score. Re-process it so
                        # the exporter can restore the missing fact_jobs row.
                        fact_job_exists = False

                        # ScoreRepository owns the shared DuckDB connection
                        # used by the engine repositories. Use that same
                        # connection when verifying whether the job was
                        # actually persisted to fact_jobs.
                        fact_connection = self._score_repo.connection

                        fact_job_exists = (
                            fact_connection.execute(
                                """
                                SELECT 1
                                FROM fact_jobs
                                WHERE job_id = ?
                                LIMIT 1
                                """,
                                [canonical_job_id],
                            ).fetchone()
                            is not None
                        )

                        if not fact_job_exists:
                            logger.warning(
                                "Recovering orphaned scored job %s: "
                                "profile score exists but fact_jobs row is missing",
                                canonical_job_id,
                            )
                            new_jobs.append(job)
                        else:
                            self._registry.mark_seen(job)
                            seen_count += 1

                else:
                    self._registry.mark_seen(job)
                    seen_count += 1

            except Exception as exc:
                logger.warning(
                    "Registry operation failed for "
                    "job %s: %s",
                    job.job_id,
                    exc,
                )

                # Fail-open:
                # If registry lookup fails, process the job
                # rather than silently losing it.
                new_jobs.append(job)

        return new_jobs, seen_count

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def execute(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        """
        Execute one search request.

        This method only fetches jobs.
        No validation, scoring, deduplication, or export occurs here.
        """
        if not self._connectors:
            raise RuntimeError(
                "No connectors configured in engine"
            )

        all_jobs: list[Job] = []

        for connector in self._connectors:
            connector_name = connector.name

            try:
                connector_jobs = connector.fetch_jobs(
                    request
                )

                all_jobs.extend(
                    connector_jobs
                )

            except Exception:
                logger.exception(
                    "Connector '%s' failed for '%s'",
                    connector_name,
                    request.keyword,
                )

                continue

        return all_jobs

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------

    def run(
        self,
        requests: SearchRequest | Iterable[SearchRequest],
        destination: Path,
        profile_type: str | None = None,
    ) -> ExecutionSummary:
        """
        Execute one or more search requests.

        Incremental pipeline:

            1. Fetch ALL requested searches
            2. Registry NEW/SEEN classification
            3. Only NEW jobs enter processing pipeline
            4. In-memory deduplication
            5. Validation
            6. Profile filtering
            7. Intelligence extraction
            8. Scoring
            9. Export
            10. Session completion

        Existing jobs:
            - are NOT scored
            - are NOT exported
            - are NOT inserted into fact_jobs again
            - are only marked as seen

        Args:
            requests:
                One SearchRequest or iterable of SearchRequest.

            destination:
                Export destination.

            profile_type:
                Active profile, e.g. crm_manager.
        """
        if not self._connectors:
            raise RuntimeError(
                "No connectors configured in engine"
            )

        try:
            # ----------------------------------------------------------
            # Initialize repositories
            # ----------------------------------------------------------

            self._ensure_repositories()

            # ----------------------------------------------------------
            # Load profile/scoring configuration
            # ----------------------------------------------------------

            profile = None

            if profile_type:
                from jobs.profiles.loader import (
                    ConfigLoader,
                )

                profile = ConfigLoader.load_profile(
                    profile_type
                )

                self._ensure_scoring_components(
                    profile_type,
                    profile,
                )

            # ----------------------------------------------------------
            # Connector metadata
            # ----------------------------------------------------------

            first_connector = self._connectors[0]

            portal = getattr(
                first_connector,
                "PORTAL",
                Portal.UNKNOWN,
            )

            connector_type = getattr(
                first_connector,
                "CONNECTOR_TYPE",
                ConnectorType.UNKNOWN,
            )

            connector_version = getattr(
                first_connector,
                "VERSION",
                "0.0.0",
            )

            if portal == Portal.UNKNOWN:
                raise RuntimeError(
                    "Connector must define a valid PORTAL."
                )

            if connector_type == ConnectorType.UNKNOWN:
                raise RuntimeError(
                    "Connector must define a valid CONNECTOR_TYPE."
                )

            export_format = getattr(
                self._exporter,
                "EXPORT_FORMAT",
                ExportFormat.DUCKDB,
            )

            started_at = datetime.now(UTC)

            # ----------------------------------------------------------
            # Normalize request list
            # ----------------------------------------------------------

            request_list = (
                [requests]
                if isinstance(
                    requests,
                    SearchRequest,
                )
                else list(requests)
            )

            if not request_list:
                raise RuntimeError(
                    "No search requests provided"
                )

            # ----------------------------------------------------------
            # Start search session
            # ----------------------------------------------------------

            if self._session_repo is None:
                raise RuntimeError(
                    "Session repository not initialized"
                )

            session_id = (
                self._session_repo.start_session(
                    portal=portal,
                    keyword=request_list[0].keyword,
                    connector_version=connector_version,
                    location=request_list[0].location,
                    connector_type=connector_type,
                    search_type=SearchType.MANUAL,
                    export_format=export_format,
                    destination=self._destination,
                    metadata={
                        "cli_args": {
                            "total_searches": len(
                                request_list
                            ),
                            "keywords": [
                                request.keyword
                                for request in request_list
                            ],
                        },
                        "python_version":
                            platform.python_version(),
                        "profile_type":
                            profile_type,
                    },
                )
            )

            # ----------------------------------------------------------
            # Search cache — skip recently fetched keyword+city pairs
            # ----------------------------------------------------------
            search_cache = None
            skipped_by_cache = 0
            try:
                if self._connection is not None:
                    search_cache = SearchCache(
                        self._connection,
                        ttl_days=3,   # 3-day cache: fresh but fast
                    )
            except Exception as _exc:
                logger.warning(
                    "Failed to initialize search cache: %s",
                    _exc,
                )
                search_cache = None

            # ----------------------------------------------------------
            # Give connectors current session context
            # ----------------------------------------------------------

            for connector in self._connectors:
                self._set_connector_context(
                    connector,
                    session_id,
                    profile_type=profile_type,
                )

            # ----------------------------------------------------------
            # Fetch
            # ----------------------------------------------------------

            all_jobs: list[Job] = []
            errors: list[str] = []

            # ----------------------------------------------------------
            # Rejection tracking — captures job flow through pipeline
            # ----------------------------------------------------------
            rejection_stats = {
                "raw_fetched": 0,
                "already_seen": 0,
                "validation_failed": 0,
                "profile_filter_rejected": 0,
                "exported": 0,
            }

            # Per-keyword-per-city metrics for later reporting
            per_search_metrics: list[dict] = []

            fetch_started_monotonic = time.monotonic()

            for index, request in enumerate(
                request_list,
                1,
            ):
                search_started_monotonic = time.monotonic()
                jobs_before = len(all_jobs)

                logger.info(
                    "[%03d/%03d] START | %s | %s | %s",
                    index,
                    len(request_list),
                    self._connectors[0].name if self._connectors else "unknown",
                    request.keyword,
                    request.location,
                )

                # ---------------------------------------------------
                # Cache check: skip if same portal+keyword+city
                # was searched recently
                # ---------------------------------------------------
                if search_cache is not None:
                    portal_name = (
                        self._connectors[0].name.lower()
                        if self._connectors else ""
                    )
                    try:
                        if search_cache.should_skip(
                            portal=portal_name,
                            keyword=request.keyword,
                            location=request.location,
                        ):
                            skipped_by_cache += 1
                            logger.info(
                                "[%03d/%03d] SKIP (cache) | %s | %s | %s",
                                index,
                                len(request_list),
                                portal_name,
                                request.keyword,
                                request.location,
                            )
                            continue
                    except Exception as _exc:
                        logger.debug("Cache check failed: %s", _exc)

                try:
                    # Each SearchRequest gets its own raw-data ID.
                    # The overall execution/session ID remains unchanged.
                    raw_search_id = uuid4()

                    for connector in self._connectors:
                        if hasattr(
                            connector,
                            "set_raw_search_id",
                        ):
                            connector.set_raw_search_id(
                                raw_search_id
                            )

                    jobs = self.execute(request)
                    all_jobs.extend(jobs)

                    search_elapsed = (
                        time.monotonic()
                        - search_started_monotonic
                    )

                    # Record per-search metrics
                    per_search_metrics.append({
                        "index": index,
                        "keyword": request.keyword,
                        "location": request.location,
                        "jobs_found": len(jobs),
                        "jobs_new": len(all_jobs) - jobs_before,
                        "elapsed_seconds": round(search_elapsed, 2),
                        "raw_jobs_from_connector": len(jobs),
                    })

                    rejection_stats["raw_fetched"] += len(jobs)

                    # Record in cache
                    if search_cache is not None:
                        try:
                            search_cache.record(
                                portal=portal_name,
                                keyword=request.keyword,
                                location=request.location,
                                jobs_found=len(jobs),
                                jobs_exported=0,
                            )
                        except Exception as _exc:
                            logger.debug("Cache record failed: %s", _exc)
                    run_elapsed = (
                        time.monotonic()
                        - fetch_started_monotonic
                    )
                    average_elapsed = run_elapsed / index
                    remaining_searches = len(request_list) - index
                    eta_seconds = average_elapsed * remaining_searches

                    logger.info(
                        "[%03d/%03d] DONE | %s | %s | "
                        "jobs=%d | elapsed=%.1fs | total=%.1fmin | ETA=%.1fmin",
                        index,
                        len(request_list),
                        request.keyword,
                        request.location,
                        len(all_jobs) - jobs_before,
                        search_elapsed,
                        run_elapsed / 60,
                        eta_seconds / 60,
                    )

                except Exception as exc:
                    search_elapsed = (
                        time.monotonic()
                        - search_started_monotonic
                    )
                    logger.exception(
                        "[%03d/%03d] FAILED | %s | %s | elapsed=%.1fs",
                        index,
                        len(request_list),
                        request.keyword,
                        request.location,
                        search_elapsed,
                    )
                    errors.append(
                        f"Search '{request.keyword}' "
                        f"failed: {exc}"
                    )

                    continue

            total_jobs = len(all_jobs)

            logger.info(
                "Total jobs collected: %s",
                total_jobs,
            )

            # ----------------------------------------------------------
            # Step 1:
            # Registry-based NEW vs SEEN classification
            # ----------------------------------------------------------

            new_jobs, seen_jobs_count = (
                self._classify_registry_jobs(
                    all_jobs,
                    profile_type=profile_type,
                )
            )

            logger.info(
                "Registry classification: "
                "NEW=%s, SEEN=%s",
                len(new_jobs),
                seen_jobs_count,
            )

            # ----------------------------------------------------------
            # Step 2:
            # Deduplicate ONLY NEW jobs
            # ----------------------------------------------------------

            deduplicated_new = (
                self._deduplicator.deduplicate(
                    new_jobs
                )
            )

            duplicate_jobs_removed = (
                len(new_jobs)
                - len(deduplicated_new)
            )

            logger.info(
                "NEW jobs after deduplication: %s "
                "(duplicates removed: %s)",
                len(deduplicated_new),
                duplicate_jobs_removed,
            )

            # ----------------------------------------------------------
            # Step 3:
            # Validate ONLY NEW jobs
            # ----------------------------------------------------------

            valid_jobs, invalid_jobs = (
                self._validator.validate_many(
                    deduplicated_new
                )
            )

            logger.info(
                "NEW jobs validation: "
                "valid=%s invalid=%s",
                len(valid_jobs),
                len(invalid_jobs),
            )

            print("")
            print("=" * 72)
            print("ENGINE VALIDATION RECONCILIATION")
            print("=" * 72)
            print(
                f"NEW after deduplication : {len(deduplicated_new):,}"
            )
            print(
                f"Validator ACCEPTED      : {len(valid_jobs):,}"
            )
            print(
                f"Validator REJECTED      : {len(invalid_jobs):,}"
            )
            print(
                f"Validation reconciled   : "
                f"{len(valid_jobs) + len(invalid_jobs):,}"
            )
            print("=" * 72)
            print("")

            # ----------------------------------------------------------
            # Registry lifecycle:
            # Validator-rejected NEW jobs must not remain NEW forever.
            # They have completed processing and should become REJECTED.
            # ----------------------------------------------------------

            # Track validation failures
            rejection_stats["validation_failed"] = len(invalid_jobs)

            if invalid_jobs and self._registry is not None:
                for job in invalid_jobs:
                    try:
                        self._registry.mark_rejected(
                            job,
                            reason="Validation rejected",
                        )
                    except Exception as exc:
                        msg = str(exc)
                        if "Invalid transition" not in msg:
                            logger.warning(
                                "Failed to mark validation-rejected "
                                "job %s as REJECTED: %s",
                                job.job_id,
                                exc,
                            )

            # ----------------------------------------------------------
            # Step 3.5:
            # Profile filtering ONLY NEW jobs
            # ----------------------------------------------------------

            if profile_type and profile:
                filter_obj = (
                    self._profile_filters.get(
                        profile_type
                    )
                )

                if filter_obj:
                    (
                        filtered_jobs,
                        rejected_jobs,
                    ) = filter_obj.filter_jobs(
                        valid_jobs
                    )

                    logger.info(
                        "Profile filtering: "
                        "accepted=%s rejected=%s",
                        len(filtered_jobs),
                        len(rejected_jobs),
                    )

                    # Track profile filter rejections
                    rejection_stats["profile_filter_rejected"] = len(rejected_jobs)

                    # Profile-rejected NEW jobs have completed the
                    # profile decision and must not remain NEW.
                    if rejected_jobs and self._registry is not None:
                        for job in rejected_jobs:
                            try:
                                self._registry.mark_rejected(
                                    job,
                                    reason="Profile filter rejected",
                                )
                            except Exception as exc:
                                # "Invalid transition: REJECTED -> REJECTED"
                                # is expected when the job was already
                                # rejected in a previous run. Ignore.
                                msg = str(exc)
                                if "Invalid transition" in msg:
                                    pass  # already rejected — fine
                                else:
                                    logger.warning(
                                        "Failed to mark profile-rejected "
                                        "job %s as REJECTED: %s",
                                        job.job_id,
                                        exc,
                                    )

                    valid_jobs = filtered_jobs

            # ----------------------------------------------------------
            # Step 4:
            # Score ONLY NEW jobs
            # ----------------------------------------------------------

            if profile_type:
                logger.info(
                    "Scoring enabled for profile: %s",
                    profile_type,
                )

            else:
                logger.info(
                    "Scoring disabled: "
                    "no profile_type provided"
                )

            if valid_jobs and profile_type:

                extractor = (
                    self._extractors.get(
                        profile_type
                    )
                )

                scoring_engine = (
                    self._scoring_engines.get(
                        profile_type
                    )
                )
                if (
                    extractor is None
                    or scoring_engine is None
                ):
                    raise RuntimeError(
                        "Scoring components unavailable "
                        f"for profile: {profile_type}"
                    )

                if self._score_repo is None:
                    raise RuntimeError(
                        "Score repository not initialized"
                    )

                logger.info(
                    "Starting scoring for %s NEW jobs",
                    len(valid_jobs),
                )

                # Batched scoring:
                #   - score every job in memory
                #   - flush every 100 rows in ONE DuckDB transaction
                #   - fall back to per-row save if save_many() unavailable
                BATCH_SIZE = 100
                batch: list[tuple] = []
                total_saved = 0

                has_save_many = hasattr(
                    self._score_repo, "save_many"
                )

                def _flush(batch_rows: list[tuple]) -> None:
                    nonlocal total_saved
                    if not batch_rows:
                        return
                    if has_save_many:
                        self._score_repo.save_many(batch_rows)
                        total_saved += len(batch_rows)
                        logger.info(
                            "Flushed %s score rows (total=%s)",
                            len(batch_rows),
                            total_saved,
                        )
                    else:
                        # Fallback path (unchanged behavior)
                        for (
                            j_id,
                            p_id,
                            s_id,
                            s_result,
                            p_ver,
                        ) in batch_rows:
                            self._score_repo.save_score_result(
                                job_id=j_id,
                                profile_id=p_id,
                                search_session_id=s_id,
                                score_result=s_result,
                                pipeline_version=p_ver,
                            )
                            total_saved += 1

                for index, job in enumerate(
                    valid_jobs,
                    1,
                ):
                    try:
                        logger.info(
                            "Scoring NEW job %s/%s: %s",
                            index,
                            len(valid_jobs),
                            job.job_id,
                        )

                        intelligence = (
                            extractor.extract_from_job(job)
                        )

                        result = scoring_engine.score_job(
                            intelligence,
                            job_title=job.title,
                            job_description=job.description,
                        )

                        canonical_job_id = self._canonical_job_id(job)

                        batch.append(
                            (
                                canonical_job_id,
                                profile_type,
                                session_id,
                                result,
                                AI_PIPELINE_VERSION,
                            )
                        )

                        if len(batch) >= BATCH_SIZE:
                            _flush(batch)
                            batch.clear()

                    except Exception as exc:
                        logger.exception(
                            "Failed to score job %s: %s",
                            job.job_id,
                            exc,
                        )
                        raise

                # Flush any remaining rows
                _flush(batch)
                batch.clear()

                logger.info(
                    "Scoring complete: %s rows saved",
                    total_saved,
                )

            else:
                logger.info(
                    "No NEW jobs require scoring"
                )

            # ----------------------------------------------------------
            # Step 5:
            # Export the exact NEW jobs that already passed validation
            # and profile filtering in Step 3/3.5.
            # ----------------------------------------------------------

            valid_new = list(valid_jobs)

            # Track exported
            rejection_stats["exported"] = len(valid_new)

            if valid_new:
                self._exporter.export(
                    valid_new,
                    destination,
                )

                if self._registry is not None:
                    try:
                        self._registry.mark_seen_many(
                            valid_new
                        )

                        logger.debug(
                            "Marked %s jobs as SEEN "
                            "after export",
                            len(valid_new),
                        )

                    except Exception as exc:
                        logger.warning(
                            "Failed to mark jobs as "
                            "seen after export: %s",
                            exc,
                        )

            # ----------------------------------------------------------
            # Step 6:
            # Session completion
            # ----------------------------------------------------------

            duration_ms = int(
                (
                    datetime.now(UTC)
                    - started_at
                ).total_seconds()
                * 1000
            )

            if self._session_repo is None:
                raise RuntimeError(
                    "Session repository not initialized"
                )

            # ----------------------------------------------------------
            # Save per-search metrics to CSV (avoid 10KB metadata limit)
            # ----------------------------------------------------------
            metrics_csv_path = None
            if per_search_metrics:
                try:
                    import csv as _csv
                    from pathlib import Path as _Path

                    metrics_dir = _Path("output") / "session_metrics"
                    metrics_dir.mkdir(parents=True, exist_ok=True)

                    metrics_csv_path = (
                        metrics_dir
                        / f"session_{str(session_id)[:8]}_metrics.csv"
                    )

                    with metrics_csv_path.open("w", newline="") as _f:
                        writer = _csv.DictWriter(
                            _f,
                            fieldnames=[
                                "index",
                                "keyword",
                                "location",
                                "jobs_found",
                                "jobs_new",
                                "elapsed_seconds",
                                "raw_jobs_from_connector",
                            ],
                        )
                        writer.writeheader()
                        writer.writerows(per_search_metrics)

                    logger.info(
                        "Per-search metrics saved: %s (%d rows)",
                        metrics_csv_path,
                        len(per_search_metrics),
                    )
                except Exception as _exc:
                    logger.warning(
                        "Failed to save per-search metrics CSV: %s",
                        _exc,
                    )
                    metrics_csv_path = None

            # Compute already_seen count
            rejection_stats["already_seen"] = (
                rejection_stats["raw_fetched"]
                - rejection_stats["validation_failed"]
                - rejection_stats["profile_filter_rejected"]
                - rejection_stats["exported"]
            )

            # Summary stats for metadata (keep < 10 KB)
            _metrics_summary = {
                "total_searches": len(request_list),
                "skipped_by_cache": skipped_by_cache,
                "metrics_csv_path": (
                    str(metrics_csv_path)
                    if metrics_csv_path else None
                ),
                "rejection_stats": rejection_stats,
            }

            if errors:

                self._session_repo.complete_session(
                    execution_id=session_id,
                    status=SearchStatus.FAILED,
                    finished_reason=(
                        FinishedReason.FAILED
                    ),
                    jobs_found=total_jobs,
                    duplicates_removed=(
                        duplicate_jobs_removed
                    ),
                    valid_jobs=len(valid_jobs),
                    invalid_jobs=len(invalid_jobs),
                    exported_jobs=len(valid_new),
                    duration_ms=duration_ms,
                    error_message="; ".join(
                        errors[:3]
                    ),
                    metadata=_metrics_summary,
                )

            else:

                self._session_repo.complete_session(
                    execution_id=session_id,
                    status=SearchStatus.COMPLETED,
                    finished_reason=(
                        FinishedReason.SUCCESS
                    ),
                    jobs_found=total_jobs,
                    duplicates_removed=(
                        duplicate_jobs_removed
                    ),
                    valid_jobs=len(valid_jobs),
                    invalid_jobs=len(invalid_jobs),
                    exported_jobs=len(valid_new),
                    duration_ms=duration_ms,
                    metadata=_metrics_summary,
                )

            # ----------------------------------------------------------
            # Summary
            # ----------------------------------------------------------

            connectors_used = [
                connector.name
                for connector in self._connectors
            ]

            return ExecutionSummary(
                execution_id=session_id,
                connectors_used=connectors_used,
                total_jobs=total_jobs,
                duplicate_jobs_removed=(
                    duplicate_jobs_removed
                ),
                valid_jobs=len(valid_jobs),
                invalid_jobs=len(invalid_jobs),
                exported_jobs=len(valid_new),
                destination=destination,
                errors=errors,
            )

        finally:
            self.close()

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    def close(self) -> None:
        """
        Close database connection and clear runtime components.
        """
        if self._connection is not None:
            self._connection.close()

            self._connection = None
            self._session_repo = None
            self._raw_repo = None
            self._registry_repo = None
            self._registry = None
            self._score_repo = None

            self._extractors.clear()
            self._scoring_engines.clear()
            self._profile_filters.clear()


# =============================================================================
# END OF FILE
# =============================================================================
