"""
Application tracking API.

Application ownership is derived from the authenticated JWT.
Clients must never provide user_id.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from api.application_store import (
    count_dead_reports,
    delete_application,
    get_application,
    get_applications,
    get_application_summary,
    report_job_dead,
    upsert_application,
)
from api.account_store import get_profile
from api.auth import get_authenticated_user


router = APIRouter(prefix="/applications")

bearer_scheme = HTTPBearer()


ApplicationStatus = Literal[
    "saved",
    "pending",
    "applied",
    "interview",
    "rejected",
    "offer",
    "not_relevant",
]


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus
    applied_at: str | None = None
    notes: str = ""


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
) -> dict:
    return get_authenticated_user(
        credentials.credentials
    )


@router.get("/{job_id}")
async def get_application_status(
    job_id: str,
    user: Annotated[dict, Depends(get_current_user)],
):
    application = get_application(
        user["user_id"],
        job_id,
    )

    return {
        "application": application,
    }


@router.put("/{job_id}")
async def update_application(
    job_id: str,
    payload: ApplicationUpdate,
    user: Annotated[dict, Depends(get_current_user)],
):
    try:
        profile = get_profile(user["user_id"])

        if profile is None:
            raise HTTPException(
                status_code=400,
                detail="Complete your profile before updating application status.",
            )

        application = upsert_application(
            user_id=user["user_id"],
            job_id=job_id,
            profile_id=profile["profile_id"],
            status=payload.status,
            applied_at=payload.applied_at,
            notes=payload.notes,
        )

        return {
            "application": application,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save application: {exc}",
        ) from exc


@router.delete("/{job_id}")
async def remove_application(
    job_id: str,
    user: Annotated[dict, Depends(get_current_user)],
):
    delete_application(
        user["user_id"],
        job_id,
    )

    return {
        "success": True,
    }


@router.get("")
async def applications(
    user: Annotated[dict, Depends(get_current_user)],
    job_id: Annotated[list[str] | None, Query()] = None,
):
    """
    Return application records belonging only to the
    authenticated user.

    With job_id parameters:
        Return status records for those jobs.

    Without job_id:
        Return the authenticated user's status summary.
    """

    user_id = user["user_id"]

    if job_id:
        return {
            "applications": get_applications(
                user_id,
                job_id,
            )
        }

    return get_application_summary(user_id)

# ============================================================
# Job-liveness: user reports a job as dead
# ============================================================

@router.post("/{job_id}/report-dead")
async def report_dead(
    job_id: str,
    user: Annotated[dict, Depends(get_current_user)],
):
    """
    User reports a job URL as dead/expired/no-longer-applyable.

    Records this user's report idempotently and returns the current
    distinct-user report count. The pipeline-side worker reads this
    table daily and flips fact_jobs.is_active = FALSE once the
    threshold (5 distinct users) is reached.
    """
    try:
        result = report_job_dead(user["user_id"], job_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record report: {exc}",
        ) from exc

    return {
        "job_id": job_id,
        "reported_dead_count": result["dead_report_count"],
        "hidden_for_you": True,
    }


@router.get("/{job_id}/dead-report-count")
async def dead_report_count(
    job_id: str,
    user: Annotated[dict, Depends(get_current_user)],
):
    """Return how many distinct users have reported this job as dead."""
    return {
        "job_id": job_id,
        "reported_dead_count": count_dead_reports(job_id),
    }

