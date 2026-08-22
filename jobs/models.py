"""
Shared job model for all job portals.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Job:
    source: str
    title: str
    company: str
    job_url: str

    location: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    posted_date: Optional[str] = None

    job_id: Optional[str] = None
    company_url: Optional[str] = None
    company_logo: Optional[str] = None

    work_mode: Optional[str] = None          # Remote / Hybrid / Onsite
    experience: Optional[str] = None         # 3-5 Years
    skills: Optional[str] = None
    department: Optional[str] = None

    easy_apply: bool = False
    sponsored: bool = False