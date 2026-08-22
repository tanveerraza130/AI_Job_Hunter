-- =============================================================================
-- AI Job Hunter - Database Schema
-- =============================================================================

-- =============================================================================
-- Session Repository
-- =============================================================================

CREATE TABLE IF NOT EXISTS search_session (
    execution_id UUID PRIMARY KEY,
    user_id UUID,
    workspace_id UUID,
    saved_search_id UUID,
    portal VARCHAR NOT NULL,
    connector_type VARCHAR,
    connector_version VARCHAR,
    engine_version VARCHAR,
    ai_pipeline_version VARCHAR,
    search_type VARCHAR,
    keyword VARCHAR NOT NULL,
    location VARCHAR,
    export_format VARCHAR,
    destination VARCHAR,
    status VARCHAR NOT NULL,
    finished_reason VARCHAR,
    created_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL,
    duration_ms BIGINT,
    jobs_found INTEGER,
    duplicates_removed INTEGER,
    valid_jobs INTEGER,
    invalid_jobs INTEGER,
    exported_jobs INTEGER,
    error_message TEXT,
    metadata JSON,
    archived_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_session_user ON search_session(user_id);
CREATE INDEX IF NOT EXISTS idx_session_started ON search_session(started_at);
CREATE INDEX IF NOT EXISTS idx_session_status ON search_session(status);
CREATE INDEX IF NOT EXISTS idx_session_portal ON search_session(portal);
CREATE INDEX IF NOT EXISTS idx_session_search_type ON search_session(search_type);
CREATE INDEX IF NOT EXISTS idx_session_archived ON search_session(archived_at);

-- =============================================================================
-- Raw Data Repository
-- =============================================================================

CREATE TABLE IF NOT EXISTS portal_raw_data (
    search_id UUID NOT NULL,
    portal VARCHAR NOT NULL,
    keyword VARCHAR,
    location VARCHAR,
    page_no INTEGER NOT NULL,
    captured_at TIMESTAMP NOT NULL,
    request_url VARCHAR,
    request_method VARCHAR,
    response_status INTEGER,
    request_headers JSON,
    request_query JSON,
    response_json JSON,
    jobs_count INTEGER,
    response_size_bytes BIGINT,
    UNIQUE(search_id, portal, page_no)
);

CREATE INDEX IF NOT EXISTS idx_raw_search ON portal_raw_data(search_id);
CREATE INDEX IF NOT EXISTS idx_raw_portal ON portal_raw_data(portal);
CREATE INDEX IF NOT EXISTS idx_raw_captured ON portal_raw_data(captured_at);

-- =============================================================================
-- Job Registry
-- =============================================================================

CREATE TABLE IF NOT EXISTS job_registry (
    fingerprint CHAR(64) PRIMARY KEY,
    portal VARCHAR NOT NULL,
    portal_job_id VARCHAR,
    company VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    location VARCHAR,
    status VARCHAR NOT NULL,
    first_seen_at TIMESTAMP NOT NULL,
    last_seen_at TIMESTAMP NOT NULL,
    applied_at TIMESTAMP,
    rejected_at TIMESTAMP,
    expired_at TIMESTAMP,
    metadata JSON
);

CREATE INDEX IF NOT EXISTS idx_job_registry_status ON job_registry(status);
CREATE INDEX IF NOT EXISTS idx_job_registry_last_seen ON job_registry(last_seen_at);
CREATE INDEX IF NOT EXISTS idx_job_registry_portal ON job_registry(portal);

-- =============================================================================
-- Job Scores
-- =============================================================================

CREATE TABLE IF NOT EXISTS fact_job_scores (
    job_id VARCHAR NOT NULL,
    profile_id VARCHAR NOT NULL,
    search_session_id UUID NOT NULL,
    overall_score FLOAT NOT NULL,
    skill_score FLOAT,
    tool_score FLOAT,
    experience_score FLOAT,
    salary_score FLOAT,
    work_mode_score FLOAT,
    score_breakdown JSON,
    scoring_version VARCHAR,
    pipeline_version VARCHAR,
    scored_at TIMESTAMP NOT NULL,
    PRIMARY KEY (job_id, profile_id, search_session_id)
);

CREATE INDEX IF NOT EXISTS idx_job_scores_job_id ON fact_job_scores(job_id);
CREATE INDEX IF NOT EXISTS idx_job_scores_profile_id ON fact_job_scores(profile_id);
CREATE INDEX IF NOT EXISTS idx_job_scores_search_session ON fact_job_scores(search_session_id);
CREATE INDEX IF NOT EXISTS idx_job_scores_overall ON fact_job_scores(overall_score);

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================