"""
Application tracking API.
"""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.application_store import (
    delete_application,
    get_application,
    get_application_summary,
    upsert_application,
)


router = APIRouter(prefix="/applications")


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
    profile_id: str = Field(min_length=1)
    status: ApplicationStatus
    applied_at: str | None = None
    notes: str = ""


@router.get("/{job_id}")
async def get_application_status(
    job_id: str,
    profile_id: str,
):
    return {
        "application": get_application(
            job_id,
            profile_id,
        )
    }


@router.put("/{job_id}")
async def update_application(
    job_id: str,
    payload: ApplicationUpdate,
):
    try:
        application = upsert_application(
            job_id=job_id,
            profile_id=payload.profile_id,
            status=payload.status,
            applied_at=payload.applied_at,
            notes=payload.notes,
        )

        return {
            "application": application
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save application: {exc}",
        ) from exc


@router.delete("/{job_id}")
async def remove_application(
    job_id: str,
    profile_id: str,
):
    delete_application(
        job_id,
        profile_id,
    )

    return {
        "success": True
    }


@router.get("")
async def application_summary(
    profile_id: str,
):
    return get_application_summary(profile_id)
