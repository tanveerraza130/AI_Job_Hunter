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
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import duckdb

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
    ) -> None:
        """
        Set repository context on connectors that support it.
        """
        if hasattr(connector, "set_repositories"):
            connector.set_repositories(
                self._raw_repo,
                session_id,
            )

    # ------------------------------------------------------------------
    # Registry
    # ------------------------------------------------------------------

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
                    and not self._score_repo.has_score(
                        job_id=job.job_id,
                        profile_id=profile_type,
                    )
                ):
                    # Job exists globally, but this profile has
                    # not processed it yet. Allow profile-specific
                    # processing.
                    new_jobs.append(job)

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

            except Exception as exc:
                logger.error(
                    "Connector '%s' failed for '%s': %s",
                    connector_name,
                    request.keyword,
                    exc,
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
            # Give connectors current session context
            # ----------------------------------------------------------

            for connector in self._connectors:
                self._set_connector_context(
                    connector,
                    session_id,
                )

            # ----------------------------------------------------------
            # Fetch
            # ----------------------------------------------------------

            all_jobs: list[Job] = []
            errors: list[str] = []

            for index, request in enumerate(
                request_list,
                1,
            ):
                logger.info(
                    "Search %s/%s: %s in %s",
                    index,
                    len(request_list),
                    request.keyword,
                    request.location,
                )

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

                    jobs = self.execute(
                        request
                    )

                    all_jobs.extend(jobs)

                except Exception as exc:
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

                        # ----------------------------------------------
                        # Intelligence extraction
                        # ----------------------------------------------

                        intelligence = (
                            extractor.extract_from_job(
                                job
                            )
                        )

                        logger.info(
                            "Intelligence extracted for %s",
                            job.job_id,
                        )
                        # ----------------------------------------------
                        # Scoring
                        # ----------------------------------------------

                        result = (
                            scoring_engine.score_job(
                                intelligence,
                                job_title=job.title,
                                job_description=(
                                    job.description
                                ),
                            )
                        )

                        logger.info(
                            "Score computed for %s: %s",
                            job.job_id,
                            result.score,
                        )

                        # ----------------------------------------------
                        # Persist score
                        # ----------------------------------------------

                        canonical_job_id = (
                            f"{job.portal}:{job.job_id}"
                            if job.portal and ':' not in str(job.job_id)
                            else str(job.job_id)
                        )
                        self._score_repo.save_score_result(
                            job_id=canonical_job_id,
                            profile_id=profile_type,
                            search_session_id=session_id,
                            score_result=result,
                            pipeline_version=(
                                AI_PIPELINE_VERSION
                            ),
                        )

                        logger.info(
                            "Score saved for %s",
                            job.job_id,
                        )

                    except Exception as exc:
                        logger.exception(
                            "Failed to score job %s: %s",
                            job.job_id,
                            exc,
                        )

                        raise

            else:
                logger.info(
                    "No NEW jobs require scoring"
                )

            # ----------------------------------------------------------
            # Step 5:
            # Export ONLY NEW valid jobs
            # ----------------------------------------------------------

            valid_new: list[Job] = []

            if new_jobs:

                # IMPORTANT:
                # Re-deduplicate the exact NEW set used for export.
                deduplicated_export_jobs = (
                    self._deduplicator.deduplicate(
                        new_jobs
                    )
                )

                valid_new, invalid_new = (
                    self._validator.validate_many(
                        deduplicated_export_jobs
                    )
                )

                # Apply profile filter to export set as well.
                if profile_type and profile:
                    filter_obj = (
                        self._profile_filters.get(
                            profile_type
                        )
                    )

                    if filter_obj:
                        (
                            valid_new,
                            rejected_new,
                        ) = filter_obj.filter_jobs(
                            valid_new
                        )

                        logger.info(
                            "Export filtering: "
                            "accepted=%s rejected=%s",
                            len(valid_new),
                            len(rejected_new),
                        )

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
