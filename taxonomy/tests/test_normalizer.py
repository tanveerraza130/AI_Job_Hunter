"""
Unit tests for normalizer.
"""

from __future__ import annotations

from normalizer import Normalizer


def test_normalize_lowercase() -> None:
    """Test lowercase normalization."""
    normalizer = Normalizer()
    assert normalizer.normalize("Google Analytics") == "google analytics"


def test_normalize_strip() -> None:
    """Test whitespace stripping."""
    normalizer = Normalizer()
    assert normalizer.normalize("  google analytics  ") == "google analytics"


def test_normalize_collapse_spaces() -> None:
    """Test space collapsing."""
    normalizer = Normalizer()
    assert normalizer.normalize("google   analytics") == "google analytics"


def test_normalize_ampersand() -> None:
    """Test ampersand normalization."""
    normalizer = Normalizer()
    assert normalizer.normalize("Marketing & Sales") == "marketing and sales"


def test_normalize_special_chars() -> None:
    """Test special character removal."""
    normalizer = Normalizer()
    result = normalizer.normalize("A/B Testing!")
    assert "!" not in result
    assert "/" not in result or "or" in result