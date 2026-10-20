"""
Short-lived storage for Google OAuth state and authorization codes.

Uses a separate SQLite database so existing DuckDB schemas remain
unchanged. State and authorization codes are stored as SHA-256 hashes.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager
from collections.abc import Iterator
from pathlib import Path
from typing import Any


DB_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "oauth_transactions.sqlite3"
)

STATE_TTL_SECONDS = 600
CODE_TTL_SECONDS = 120


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=10,
        isolation_level=None,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")

    return connection


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    connection = _connect()
    try:
        yield connection
    finally:
        connection.close()


def _initialize() -> None:
    with _connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS oauth_states (
                state_hash TEXT PRIMARY KEY,
                mode TEXT NOT NULL CHECK (mode IN ('signin', 'signup')),
                expires_at INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS oauth_codes (
                code_hash TEXT PRIMARY KEY,
                state_hash TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                expires_at INTEGER NOT NULL
            )
            """
        )


def create_oauth_state(state: str, mode: str) -> None:
    if mode not in {"signin", "signup"}:
        raise ValueError("Invalid OAuth mode")

    now = int(time.time())

    with _connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "DELETE FROM oauth_states WHERE expires_at <= ?",
            (now,),
        )
        connection.execute(
            "DELETE FROM oauth_codes WHERE expires_at <= ?",
            (now,),
        )
        connection.execute(
            """
            INSERT INTO oauth_states (state_hash, mode, expires_at)
            VALUES (?, ?, ?)
            """,
            (_hash(state), mode, now + STATE_TTL_SECONDS),
        )
        connection.commit()


def consume_oauth_state(state: str) -> str | None:
    """Atomically validate and consume a state value exactly once."""
    now = int(time.time())

    with _connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """
            SELECT mode, expires_at
            FROM oauth_states
            WHERE state_hash = ?
            """,
            (_hash(state),),
        ).fetchone()

        if row is None or row["expires_at"] <= now:
            connection.execute(
                "DELETE FROM oauth_states WHERE state_hash = ?",
                (_hash(state),),
            )
            connection.commit()
            return None

        connection.execute(
            "DELETE FROM oauth_states WHERE state_hash = ?",
            (_hash(state),),
        )
        connection.commit()
        return str(row["mode"])


def create_authorization_code(
    code: str,
    state: str,
    payload: dict[str, Any],
) -> None:
    now = int(time.time())

    with _connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "DELETE FROM oauth_codes WHERE expires_at <= ?",
            (now,),
        )
        connection.execute(
            """
            INSERT INTO oauth_codes (
                code_hash, state_hash, payload_json, expires_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                _hash(code),
                _hash(state),
                json.dumps(payload, separators=(",", ":")),
                now + CODE_TTL_SECONDS,
            ),
        )
        connection.commit()


def consume_authorization_code(
    code: str,
    state: str,
) -> dict[str, Any] | None:
    """Atomically redeem a code once, bound to its original state."""
    now = int(time.time())

    with _connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """
            SELECT state_hash, payload_json, expires_at
            FROM oauth_codes
            WHERE code_hash = ?
            """,
            (_hash(code),),
        ).fetchone()

        if row is None:
            connection.commit()
            return None

        if row["state_hash"] != _hash(state):
            connection.commit()
            return None

        if row["expires_at"] <= now:
            connection.execute(
                "DELETE FROM oauth_codes WHERE code_hash = ?",
                (_hash(code),),
            )
            connection.commit()
            return None

        connection.execute(
            "DELETE FROM oauth_codes WHERE code_hash = ?",
            (_hash(code),),
        )
        connection.commit()

        payload = json.loads(row["payload_json"])
        if not isinstance(payload, dict):
            return None

        return payload


_initialize()
