-- =============================================================================
-- AI Job Hunter - LinkedIn Hiring Posts Schema
-- =============================================================================
--
-- Completely isolated from the existing Job pipeline.
-- DO NOT add this schema to jobs/storage/schema.sql.
-- =============================================================================

CREATE TABLE IF NOT EXISTS linkedin_hiring_posts (
    post_id VARCHAR PRIMARY KEY,
    post_url VARCHAR NOT NULL,

    author_name VARCHAR,
    author_url VARCHAR,
    author_headline VARCHAR,

    text TEXT NOT NULL,
    posted_at TIMESTAMP,

    company VARCHAR,
    company_url VARCHAR,
    location VARCHAR,
    role VARCHAR,

    application_url VARCHAR,
    contact_email VARCHAR,

    discovery_query VARCHAR,
    discovered_at TIMESTAMP NOT NULL,

    relevance_score DOUBLE NOT NULL DEFAULT 0,

    raw JSON
);

CREATE INDEX IF NOT EXISTS idx_linkedin_posts_posted_at
    ON linkedin_hiring_posts(posted_at);

CREATE INDEX IF NOT EXISTS idx_linkedin_posts_discovered_at
    ON linkedin_hiring_posts(discovered_at);

CREATE INDEX IF NOT EXISTS idx_linkedin_posts_role
    ON linkedin_hiring_posts(role);

CREATE INDEX IF NOT EXISTS idx_linkedin_posts_location
    ON linkedin_hiring_posts(location);
