"""
Authentication API routes.
"""

from typing import Annotated
from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from api.auth import (
    create_access_token,
    get_authenticated_user,
    hash_password,
    login_email_user,
    register_email_user,
)
from api.account_store import (
    create_password_reset_token,
    get_password_reset_token,
    get_profile,
    get_user_by_email,
    mark_password_reset_token_used,
    update_user_password,
)
from api.config import settings
from api.google_oauth import (
    authenticate_google_user,
    get_google_login_url,
)


router = APIRouter(prefix="/auth")

bearer_scheme = HTTPBearer()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class EmailCheckRequest(BaseModel):
    email: EmailStr


def _google_oauth_configured() -> bool:
    return bool(
        settings.google_client_id
        and settings.google_client_secret
        and settings.google_redirect_uri
    )


@router.get("/google/start")
async def google_start(mode: str = "signin"):
    if not _google_oauth_configured():
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is not configured.",
        )

    return RedirectResponse(
        url=get_google_login_url(mode),
        status_code=302,
    )


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str = "signin",
):
    if not _google_oauth_configured():
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is not configured.",
        )
    result = authenticate_google_user(
        code,
        mode=state,
    )

    if result.get("status") == "account_not_found":
        return RedirectResponse(
            url=(
                f"{settings.frontend_url}/signup"
                "?google_error=account_not_found"
                f"&email={result['email']}"
            ),
            status_code=302,
        )

    if result.get("status") == "account_exists":
        return RedirectResponse(
            url=(
                f"{settings.frontend_url}/signup"
                "?google_error=account_exists"
                f"&email={result['email']}"
            ),
            status_code=302,
        )

    profile = get_profile(
        result["user"]["user_id"]
    )

    result["profile_complete"] = profile is not None

    # Google signup:
    # - New account -> continue to profile form.
    # - Existing account -> treat as successful login and go to dashboard.
    if state == "signup":
        if result.get("account_created"):
            return RedirectResponse(
                url=(
                    f"{settings.frontend_url}/signup"
                    "?google_success=1"
                    f"&account_created=1"
                    f"&token={result['access_token']}"
                    f"&email={result['user']['email']}"
                ),
                status_code=302,
            )

        return RedirectResponse(
            url=(
                f"{settings.frontend_url}/dashboard"
                "?google_success=1"
                f"&token={result['access_token']}"
            ),
            status_code=302,
        )

    # Google signin with an existing account.
    # Authentication succeeds first; profile completion controls
    # whether the user continues to the profile form or dashboard.
    if result.get("profile_complete"):
        return RedirectResponse(
            url=(
                f"{settings.frontend_url}/dashboard"
                "?google_success=1"
                f"&token={result['access_token']}"
            ),
            status_code=302,
        )

    return RedirectResponse(
        url=(
            f"{settings.frontend_url}/login"
            "?google_success=1"
            "&profile_complete=0"
            f"&token={result['access_token']}"
            f"&email={result['user']['email']}"
        ),
        status_code=302,
    )


@router.post("/check-email")
async def check_email(payload: EmailCheckRequest):
    from api.account_store import get_user_by_email

    user = get_user_by_email(
        str(payload.email),
    )

    return {
        "exists": user is not None,
    }


@router.post("/forgot-password")
async def forgot_password(payload: EmailCheckRequest):
    email = str(payload.email).strip().lower()
    user = get_user_by_email(email)

    if not user:
        return {
            "status": "account_not_found",
            "message": "No account found with this email.",
        }

    if user.get("auth_provider") == "google" and not user.get("password_hash"):
        return {
            "status": "google_account",
            "message": "This account uses Google sign-in. Please continue with Google.",
        }

    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=30)
    ).replace(tzinfo=None)

    create_password_reset_token(
        user_id=user["user_id"],
        token_hash=token_hash,
        expires_at=expires_at,
    )

    return {
        "status": "reset_created",
        "message": "Password reset link created.",
        "reset_token": raw_token,
    }


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    password: str = Field(min_length=8, max_length=128)


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest):
    token_hash = hashlib.sha256(
        payload.token.encode("utf-8")
    ).hexdigest()

    reset_record = get_password_reset_token(token_hash)

    if not reset_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid password reset link.",
        )

    if reset_record["used_at"] is not None:
        raise HTTPException(
            status_code=400,
            detail="This password reset link has already been used.",
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if reset_record["expires_at"] <= now:
        raise HTTPException(
            status_code=400,
            detail="This password reset link has expired.",
        )

    update_user_password(
        reset_record["user_id"],
        hash_password(payload.password),
    )

    mark_password_reset_token_used(
        reset_record["token_id"],
    )

    return {
        "status": "password_reset",
        "message": "Password updated successfully. Please sign in.",
    }


@router.post("/register")
async def register(payload: RegisterRequest):
    return register_email_user(
        email=str(payload.email),
        password=payload.password,
    )


@router.post("/login")
async def login(payload: LoginRequest):
    result = login_email_user(
        email=str(payload.email),
        password=payload.password,
    )

    profile = get_profile(
        result["user"]["user_id"]
    )

    result["profile_complete"] = profile is not None

    return result


@router.get("/me")
async def me(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
):
    user = get_authenticated_user(
        credentials.credentials
    )

    profile = get_profile(
        user["user_id"]
    )

    return {
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "auth_provider": user["auth_provider"],
        },
        "profile": profile,
        "profile_complete": profile is not None,
    }
