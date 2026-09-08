"""
Repository for LinkedIn member hiring posts.

This repository is intentionally isolated from the existing job storage
repositories and job pipeline.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import duckdb

from jobs.linkedin_posts.models import LinkedInHiringPost


class LinkedInHiringPostRepository:
    """DuckDB persistence for LinkedIn hiring posts."""

    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        """Initialize with an active DuckDB connection."""
        self.connection = connection

    def exists(self, post_id: str) -> bool:
        """Return True when a post ID is already stored."""
        result = self.connection.execute(
            """
            SELECT 1
            FROM linkedin_hiring_posts
            WHERE post_id = ?
            LIMIT 1
            """,
            [post_id],
        ).fetchone()

        return result is not None

    def insert_or_ignore(self, post: LinkedInHiringPost) -> bool:
        """
        Insert a hiring post unless its stable LinkedIn post ID already exists.

        Returns:
            True when inserted, False when the post already exists.
        """
        if self.exists(post.post_id):
            return False

        discovered_at = post.discovered_at or datetime.now(UTC)

        raw_json = json.dumps(
            post.raw,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        self.connection.execute(
            """
            INSERT INTO linkedin_hiring_posts (
                post_id,
                post_url,
                author_name,
                author_url,
                author_headline,
                text,
                posted_at,
                company,
                company_url,
                location,
                role,
                application_url,
                contact_email,
                discovery_query,
                discovered_at,
                relevance_score,
                raw
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                post.post_id,
                post.post_url,
                post.author_name,
                post.author_url,
                post.author_headline,
                post.text,
                post.posted_at,
                post.company,
                post.company_url,
                post.location,
                post.role,
                post.application_url,
                post.contact_email,
                post.discovery_query,
                discovered_at,
                post.relevance_score,
                raw_json,
            ],
        )

        return self.exists(post.post_id)

    def get(self, post_id: str) -> LinkedInHiringPost | None:
        """Return a stored hiring post by stable LinkedIn post ID."""
        result = self.connection.execute(
            """
            SELECT
                post_id,
                post_url,
                author_name,
                author_url,
                author_headline,
                text,
                posted_at,
                company,
                company_url,
                location,
                role,
                application_url,
                contact_email,
                discovery_query,
                discovered_at,
                relevance_score,
                raw
            FROM linkedin_hiring_posts
            WHERE post_id = ?
            """,
            [post_id],
        ).fetchone()

        if result is None:
            return None

        raw = result[16]

        if isinstance(raw, str):
            raw = json.loads(raw)

        return LinkedInHiringPost(
            post_id=result[0],
            post_url=result[1],
            author_name=result[2],
            author_url=result[3],
            author_headline=result[4],
            text=result[5],
            posted_at=result[6],
            company=result[7],
            company_url=result[8],
            location=result[9],
            role=result[10],
            application_url=result[11],
            contact_email=result[12],
            discovery_query=result[13],
            discovered_at=result[14],
            relevance_score=result[15],
            raw=raw or {},
        )
