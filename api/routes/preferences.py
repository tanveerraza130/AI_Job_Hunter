"""
User dashboard preferences API.

Cross-device filter persistence.
Auth is derived from the JWT — clients never pass user_id.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from api.auth import get_authenticated_user
from api.preferences_store import (
    clear_preferences,
    get_preferences,
    save_preferences,
)


router = APIRouter(prefix="/preferences")

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
) -> dict:
    return get_authenticated_user(credentials.credentials)


class PreferencesPayload(BaseModel):
    """Dashboard filter state."""

    page: int = Field(default=1, ge=1)
    mobilePage: int = Field(default=1, ge=1)
    search: str = ""
    company: str = ""
    locations: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    portal: str = ""
    relevance: list[str] = Field(default_factory=lambda: ["gte_30"])
    sort: str = "newest"
    postedDateFrom: str = ""
    postedDateTo: str = ""


@router.get("")
async def get_my_preferences(
    user: Annotated[dict, Depends(get_current_user)],
):
    """Return saved dashboard filters for authenticated user."""
    record = get_preferences(user["user_id"])
    return {
        "preferences": record,
    }


@router.put("")
async def update_my_preferences(
    payload: PreferencesPayload,
    user: Annotated[dict, Depends(get_current_user)],
):
    """Save dashboard filters for authenticated user."""
    save_preferences(
        user["user_id"],
        payload.model_dump(),
    )
    return {"saved": True}


@router.delete("")
async def delete_my_preferences(
    user: Annotated[dict, Depends(get_current_user)],
):
    """Clear dashboard filters for authenticated user."""
    clear_preferences(user["user_id"])
    return {"cleared": True}
