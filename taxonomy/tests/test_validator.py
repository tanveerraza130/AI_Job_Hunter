"""
Unit tests for validator.
"""

from __future__ import annotations

import pytest
from validator import Validator


def test_validate_schema_pass() -> None:
    """Test schema validation passes with valid data."""
    validator = Validator()
    categories = {
        "crm_skills": [
            {"name": "Lifecycle Marketing", "aliases": ["lifecycle", "crm lifecycle"]},
        ]
    }
    assert validator.validate_schema(categories) is True


def test_validate_schema_missing_name() -> None:
    """Test schema validation fails with missing name."""
    validator = Validator()
    categories = {
        "crm_skills": [
            {"aliases": ["lifecycle"]},
        ]
    }
    assert validator.validate_schema(categories) is False


def test_validate_schema_empty_aliases() -> None:
    """Test schema validation fails with empty aliases."""
    validator = Validator()
    categories = {
        "crm_skills": [
            {"name": "Lifecycle Marketing", "aliases": []},
        ]
    }
    assert validator.validate_schema(categories) is False


def test_check_duplicates_canonical() -> None:
    """Test duplicate canonical detection."""
    validator = Validator()
    items = [
        {"name": "Lifecycle Marketing", "category": "crm_skills", "aliases": ["lifecycle"]},
        {"name": "Lifecycle Marketing", "category": "crm_concepts", "aliases": ["lifecycle"]},
    ]
    result = validator.check_duplicates(items)
    assert result["has_duplicates"] is True
    assert len(result["canonicals"]) == 1


def test_check_duplicates_alias() -> None:
    """Test duplicate alias detection."""
    validator = Validator()
    items = [
        {"name": "Lifecycle Marketing", "category": "crm_skills", "aliases": ["lifecycle"]},
        {"name": "Retention Marketing", "category": "crm_skills", "aliases": ["lifecycle"]},
    ]
    result = validator.check_duplicates(items)
    assert result["has_duplicates"] is True
    assert len(result["aliases"]) == 1


def test_check_alias_quality() -> None:
    """Test low quality alias detection."""
    validator = Validator()
    items = [
        {"name": "Lifecycle Marketing", "category": "crm_skills", "aliases": ["crm", "lifecycle"]},
    ]
    result = validator.check_alias_quality(items)
    assert result["has_low_quality"] is True
    assert len(result["items"]) == 1