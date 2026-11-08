"""
Authenticated user profile API.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from api.account_store import create_or_replace_profile, get_profile
from api.auth import get_authenticated_user


router = APIRouter(prefix="/profile")
bearer_scheme = HTTPBearer()


class ProfileUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=30)

    # Used only during first-time profile completion.
    # Once a profile exists, the stored profile_id is immutable.
    profile_id: str | None = Field(default=None, min_length=1, max_length=100)

    preferred_location: str = Field(min_length=1, max_length=150)
    role_level: str = Field(min_length=1, max_length=100)
    experience_years: str = Field(min_length=1, max_length=50)

    current_ctc_lpa: float = Field(ge=0)
    expected_ctc_lpa: float = Field(ge=0)

    resume_path: str | None = Field(default=None, max_length=500)


def current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
):
    return get_authenticated_user(credentials.credentials)


@router.get("")
async def get_my_profile(user=Depends(current_user)):
    profile = get_profile(user["user_id"])

    return {
        "profile": profile,
        "profile_complete": profile is not None,
    }


@router.put("")
async def update_my_profile(
    payload: ProfileUpdate,
    user=Depends(current_user),
):
    if payload.expected_ctc_lpa < payload.current_ctc_lpa:
        raise HTTPException(
            status_code=400,
            detail="Expected CTC cannot be lower than current CTC.",
        )

    existing_profile = get_profile(user["user_id"])

    # Profile switching: allow the user to change their active
    # profile_id, but only if they explicitly provide one.
    # If payload.profile_id is omitted, keep the existing profile.
    if payload.profile_id:
        from jobs.profiles.loader import ConfigLoader
        try:
            ConfigLoader.load_profile(payload.profile_id)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail="Unknown profile: " + payload.profile_id,
            ) from exc
        locked_profile_id = payload.profile_id
    elif existing_profile:
        locked_profile_id = existing_profile["profile_id"]
    else:
        raise HTTPException(
            status_code=400,
            detail="Job profile is required.",
        )

    profile = create_or_replace_profile(
        user_id=user["user_id"],
        full_name=payload.full_name,
        phone=payload.phone,
        profile_id=locked_profile_id,
        preferred_location=payload.preferred_location,
        role_level=payload.role_level,
        experience_years=payload.experience_years,
        current_ctc_lpa=payload.current_ctc_lpa,
        expected_ctc_lpa=payload.expected_ctc_lpa,
        resume_path=payload.resume_path,
    )

    return {
        "profile": profile,
        "profile_complete": True,
        "profile_locked": True,
        "message": "Profile updated successfully.",
    }

# ============================================================
# Profile switching (lightweight — only changes profile_id)
# ============================================================

class ActiveProfileUpdate(BaseModel):
    profile_id: str = Field(min_length=1, max_length=100)


@router.patch("/active")
async def switch_active_profile(
    payload: ActiveProfileUpdate,
    user=Depends(current_user),
):
    """
    Switch the authenticated user's active profile_id.
    Only changes profile_id — preserves all other profile fields.
    """
    from jobs.profiles.loader import ConfigLoader
    from api.account_store import create_or_replace_profile

    # Validate the profile exists on disk
    try:
        ConfigLoader.load_profile(payload.profile_id)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Unknown profile: " + payload.profile_id,
        ) from exc

    existing = get_profile(user["user_id"])
    if not existing:
        raise HTTPException(
            status_code=400,
            detail="No profile found. Complete your profile first.",
        )

    profile = create_or_replace_profile(
        user_id=user["user_id"],
        full_name=existing["full_name"],
        phone=existing["phone"],
        profile_id=payload.profile_id,
        preferred_location=existing["preferred_location"],
        role_level=existing["role_level"],
        experience_years=existing["experience_years"],
        current_ctc_lpa=existing["current_ctc_lpa"],
        expected_ctc_lpa=existing["expected_ctc_lpa"],
        resume_path=existing["resume_path"],
    )

    return {"profile_id": payload.profile_id, "profile": profile}
