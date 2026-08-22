"""
Naukri job mapper.

Converts Naukri API responses to normalized Job objects.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from jobs.identity.normalizer import Normalizer
from jobs.identity.resolver import CompanyResolver
from jobs.job import Job


def _parse_salary(salary_text: str) -> tuple[float | None, float | None, str | None]:
    """
    Parse salary text into min, max, and currency.

    Args:
        salary_text: Raw salary string from Naukri.

    Returns:
        tuple: (salary_min, salary_max, currency)
    """
    if not salary_text:
        return None, None, None

    # Remove extra spaces
    salary_text = salary_text.strip()

    # Extract currency symbol
    currency_match = re.match(r"([₹$€£])\s*", salary_text)
    currency = currency_match.group(1) if currency_match else None

    # Remove currency symbol and commas
    cleaned = re.sub(r"[₹$€£,]", "", salary_text)

    # Handle LPA suffix (Lakhs Per Annum)
    lpa_multiplier = 100000
    if "lpa" in cleaned.lower():
        cleaned = re.sub(r"lpa", "", cleaned.lower()).strip()
    else:
        lpa_multiplier = 1

    # Extract numbers
    numbers = re.findall(r"(\d+\.?\d*)", cleaned)

    if not numbers:
        return None, None, currency

    if len(numbers) == 1:
        # Single value - interpret as min, max is None
        min_val = float(numbers[0]) * lpa_multiplier
        return min_val, None, currency

    # Range: min - max
    min_val = float(numbers[0]) * lpa_multiplier
    max_val = float(numbers[1]) * lpa_multiplier
    return min_val, max_val, currency


def _parse_date(date_str: str) -> datetime | None:
    """
    Parse date string from Naukri.

    Supports:
    - Unix timestamp (milliseconds)
    - Unix timestamp (seconds)
    - YYYY-MM-DD
    - DD Mon YYYY
    - DD-MM-YYYY
    - Mon DD, YYYY

    Args:
        date_str: Raw date string.

    Returns:
        datetime | None: Parsed date or None.
    """
    if not date_str:
        return None

    value = str(date_str).strip()

    # Unix timestamp
    if value.isdigit():
        try:
            timestamp = int(value)

            # Convert milliseconds to seconds
            if timestamp > 10_000_000_000:
                timestamp /= 1000

            return datetime.fromtimestamp(timestamp)
        except Exception:
            pass

    # Supported string formats
    for fmt in ("%Y-%m-%d", "%d %b %Y", "%d-%m-%Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


def _extract_skills(description: str) -> list[str]:
    """
    Extract skills from job description.

    Args:
        description: Job description text.

    Returns:
        list[str]: List of unique skills.
    """
    if not description:
        return []

    # Common skill keywords
    skill_keywords = [
        "python", "java", "javascript", "typescript", "react", "angular", "vue",
        "node", "express", "django", "flask", "fastapi", "spring", "c++", "c#",
        "go", "rust", "ruby", "php", "html", "css", "sass", "less", "sql",
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "docker",
        "kubernetes", "aws", "azure", "gcp", "terraform", "ansible", "jenkins",
        "git", "ci/cd", "agile", "scrum", "devops", "machine learning", "ai",
        "data science", "analytics", "cloud", "microservices", "rest", "graphql",
    ]

    found_skills: set[str] = set()
    description_lower = description.lower()

    for skill in skill_keywords:
        if skill in description_lower:
            found_skills.add(skill)

    return sorted(found_skills)


def _safe_get(item: dict[str, Any], *keys: str, default: Any = "") -> str:
    """
    Safely get a value from a dictionary using multiple possible keys.

    Args:
        item: Dictionary to search.
        *keys: Keys to try in order.
        default: Default value if none of the keys exist.

    Returns:
        str: First non-empty value found, or default.
    """
    for key in keys:
        value = item.get(key)
        if value and str(value).strip():
            return str(value).strip()
    return default


def _extract_location(item: dict[str, Any]) -> str:
    """
    Extract location from Naukri API response.

    Naukri returns location in various formats:
    1. Placeholders array with type="location"
    2. Direct string: {"location": "Bangalore"}
    3. List of dictionaries: {"location": [{"label": "Bangalore"}]}
    4. Nested object: {"city": "Bangalore", "state": "Karnataka"}
    5. Multiple locations: {"locations": [{"city": "Bangalore"}]}

    Args:
        item: Raw job dictionary from Naukri API.

    Returns:
        str: Extracted location string, or "Unknown Location" if not found.
    """
    # Priority 1: Check placeholders array for location type
    placeholders = item.get("placeholders")
    if placeholders and isinstance(placeholders, list):
        for placeholder in placeholders:
            if isinstance(placeholder, dict):
                if placeholder.get("type") == "location":
                    label = placeholder.get("label")
                    if label and isinstance(label, str):
                        return label.strip()

    # Priority 2: Try direct location field
    location = item.get("location")
    if location:
        if isinstance(location, str):
            return location.strip()
        if isinstance(location, list) and location:
            # Handle list of location objects or strings
            first_loc = location[0]
            if isinstance(first_loc, dict):
                # Try common keys in location objects
                for key in ("label", "name", "city", "value", "location"):
                    if first_loc.get(key):
                        return str(first_loc[key]).strip()
                # If no common key, return first non-empty value
                for value in first_loc.values():
                    if value and isinstance(value, str):
                        return value.strip()
            elif isinstance(first_loc, str):
                return first_loc.strip()
        if isinstance(location, dict):
            # Try common keys in location dict
            for key in ("label", "name", "city", "value", "location"):
                if location.get(key):
                    return str(location[key]).strip()
            # If no common key, return first non-empty value
            for value in location.values():
                if value and isinstance(value, str):
                    return value.strip()

    # Priority 3: Try locations field (plural)
    locations = item.get("locations")
    if locations:
        if isinstance(locations, list) and locations:
            first_loc = locations[0]
            if isinstance(first_loc, dict):
                for key in ("city", "label", "name", "location"):
                    if first_loc.get(key):
                        return str(first_loc[key]).strip()
            elif isinstance(first_loc, str):
                return first_loc.strip()
        elif isinstance(locations, dict):
            for key in ("city", "label", "name", "location"):
                if locations.get(key):
                    return str(locations[key]).strip()

    # Priority 4: Try city field
    city = item.get("city")
    if city and isinstance(city, str):
        return city.strip()

    # Priority 5: Try jobLocation field (alternative key)
    job_location = item.get("jobLocation")
    if job_location and isinstance(job_location, str):
        return job_location.strip()

    # Priority 6: Try place field
    place = item.get("place")
    if place and isinstance(place, str):
        return place.strip()

    # Priority 7: Try area field
    area = item.get("area")
    if area and isinstance(area, str):
        return area.strip()

    # Priority 8: Combine location components
    city = item.get("city")
    state = item.get("state")
    country = item.get("country")

    if city or state or country:
        parts = []
        if city:
            parts.append(str(city).strip())
        if state:
            parts.append(str(state).strip())
        if country:
            parts.append(str(country).strip())
        if parts:
            return ", ".join(parts)

    return "Unknown Location"


def _normalize_field(value: str, normalize_func) -> str:
    """
    Apply normalization function to a field value.

    Args:
        value: Raw value.
        normalize_func: Normalization function.

    Returns:
        str: Normalized value.
    """
    if not value:
        return ""
    try:
        result = normalize_func(value)
        return str(result) if result else ""
    except Exception:
        return ""


def map_jobs(
    api_response: dict[str, Any],
    discovery_keyword: str = "",
) -> list[Job]:
    """
    Map Naukri API response to Job objects.

    Args:
        api_response: Raw JSON response from Naukri API.

    Returns:
        list[Job]: Normalized job objects.
    """
    jobs: list[Job] = []

    job_details = api_response.get("jobDetails", [])
    if not job_details:
        return jobs

    normalizer = Normalizer()
    resolver = CompanyResolver()

    for item in job_details:
        # Basic fields with fallback keys
        job_id = _safe_get(item, "jobId", "id", "job_id")
        title = _safe_get(item, "title", "jobTitle", "name")
        company = _safe_get(item, "companyName", "company", "company_name", "recruiterName")
        description = _safe_get(item, "jobDescription", "description", "job_desc")

        # URL - jdURL from Naukri API
        job_url = _safe_get(
            item,
            "jdURL",
            "jobUrl",
            "url",
            "job_url",
            "jobLink"
        )

        # Location - use custom extractor
        location = _extract_location(item)

        # Portal
        portal = "naukri"

        # Posted date
        posted_date_str = _safe_get(item, "postedDate", "createdDate", "date")
        posted_date = _parse_date(posted_date_str)

        # Salary
        salary_text = _safe_get(item, "salary", "salaryText", "salaryRange")
        salary_min, salary_max, salary_currency = _parse_salary(salary_text)

        # Experience
        exp_text = _safe_get(item, "experience", "exp", "experienceText")
        exp_min = None
        exp_max = None
        if exp_text:
            exp_numbers = re.findall(r"(\d+)", str(exp_text))
            if len(exp_numbers) >= 1:
                exp_min = int(exp_numbers[0])
            if len(exp_numbers) >= 2:
                exp_max = int(exp_numbers[1])

        # Employment type
        employment_type = _safe_get(item, "employmentType", "jobType", "type")

        # Skills
        skills_list = item.get("skills", [])
        if isinstance(skills_list, str):
            skills_list = [s.strip() for s in skills_list.split(",") if s.strip()]
        elif not skills_list:
            skills_list = _extract_skills(description)

        # Normalize fields
        normalized_company = resolver.resolve(company) if company else ""
        normalized_location = normalizer.normalize_location(location) if location else ""

        # Create Job object
        job = Job(
            job_id=job_id,
            title=title if title else "Unknown Position",
            company=normalized_company if normalized_company else company if company else "Unknown Company",
            location=normalized_location if normalized_location else location if location else "Unknown Location",
            description=description,
            job_url=job_url if job_url.startswith(("http://", "https://")) else f"https://www.naukri.com{job_url}" if job_url else "",
            portal=portal,
        discovery_keyword=discovery_keyword,
            posted_date=posted_date.date() if posted_date else None,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            experience_min=exp_min,
            experience_max=exp_max,
            employment_type=normalizer.normalize_employment_type(employment_type),
            skills=normalizer.normalize_skills(skills_list),
            raw=item,
        )

        jobs.append(job)

    return jobs


# =============================================================================
# END OF FILE
# =============================================================================
