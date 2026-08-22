from enum import StrEnum


class JobType(StrEnum):
    """Employment type."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"
    FREELANCE = "freelance"
    TEMPORARY = "temporary"