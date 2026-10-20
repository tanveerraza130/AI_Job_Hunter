import pytest

from api import oauth_transactions as oauth


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(oauth, "DB_PATH", tmp_path / "oauth_test.sqlite3")
    oauth._initialize()
    return oauth


def test_state_can_only_be_consumed_once(store):
    store.create_oauth_state("state-valid", "signin")

    assert store.consume_oauth_state("state-valid") == "signin"
    assert store.consume_oauth_state("state-valid") is None


def test_invalid_mode_is_rejected(store):
    with pytest.raises(ValueError, match="Invalid OAuth mode"):
        store.create_oauth_state("state-invalid", "admin")


def test_expired_state_is_rejected(store, monkeypatch):
    monkeypatch.setattr(oauth.time, "time", lambda: 1_000)
    store.create_oauth_state("state-expired", "signup")

    monkeypatch.setattr(
        oauth.time,
        "time",
        lambda: 1_000 + oauth.STATE_TTL_SECONDS,
    )
    assert store.consume_oauth_state("state-expired") is None


def test_authorization_code_can_only_be_redeemed_once(store):
    payload = {"user_id": "user-123", "profile_complete": True}
    store.create_authorization_code("code-once", "state-once", payload)

    assert store.consume_authorization_code("code-once", "state-once") == payload
    assert store.consume_authorization_code("code-once", "state-once") is None


def test_wrong_state_cannot_redeem_authorization_code(store):
    payload = {"user_id": "user-456"}
    store.create_authorization_code("code-bound", "original-state", payload)

    assert store.consume_authorization_code("code-bound", "wrong-state") is None

    # A mismatched attempt must not invalidate the legitimate exchange.
    assert (
        store.consume_authorization_code("code-bound", "original-state")
        == payload
    )


def test_expired_authorization_code_is_rejected(store, monkeypatch):
    monkeypatch.setattr(oauth.time, "time", lambda: 2_000)
    store.create_authorization_code(
        "code-expired",
        "state-expired",
        {"user_id": "user-789"},
    )

    monkeypatch.setattr(
        oauth.time,
        "time",
        lambda: 2_000 + oauth.CODE_TTL_SECONDS,
    )
    assert store.consume_authorization_code("code-expired", "state-expired") is None
