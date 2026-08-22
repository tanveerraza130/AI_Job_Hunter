"""
Test empty and null inputs.
"""

import pytest

from jobs.intelligence.models import JobIntelligence


def test_empty_jd(extractor):
    """Test that empty JD returns empty JobIntelligence."""
    intelligence = extractor.extract(title="", description="")
    assert isinstance(intelligence, JobIntelligence)
    assert len(intelligence.categories) == 0


def test_empty_title(extractor):
    """Test that empty title with description works."""
    jd = "CRM experience with CleverTap."
    intelligence = extractor.extract(title="", description=jd)
    assert isinstance(intelligence, JobIntelligence)
    # Should still extract from description
    # May or may not have items depending on aliases


def test_empty_description(extractor):
    """Test that empty description with title works."""
    intelligence = extractor.extract(title="CRM Manager", description="")
    assert isinstance(intelligence, JobIntelligence)
    # Title alone may not have enough tokens


def test_none_inputs(extractor):
    """Test that None inputs are handled gracefully."""
    intelligence = extractor.extract(title=None, description=None)
    assert isinstance(intelligence, JobIntelligence)
    assert len(intelligence.categories) == 0


def test_whitespace_only(extractor):
    """Test that whitespace-only inputs return empty."""
    intelligence = extractor.extract(title="   ", description="   ")
    assert isinstance(intelligence, JobIntelligence)
    assert len(intelligence.categories) == 0