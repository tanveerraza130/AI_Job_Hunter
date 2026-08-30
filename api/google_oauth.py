"""
Google OAuth helpers for AI Job Hunter.
"""

from __future__ import annotations

from urllib.parse import urlencode

import requests
from fastapi import HTTPException

from api.account_store import create_user, get_user_by_email
from api.auth import create_access_token
from api.config import settings


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def get_google_login_url(mode: str = "signin") -> str:
    if mode not in {"signin", "signup"}:
        mode = "signin"

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": mode,
    }

    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_google_code(code: str) -> dict:
    response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )

    if not response.ok:
        raise HTTPException(
            status_code=401,
            detail="Unable to authenticate with Google.",
        )

    return response.json()


def get_google_user(code: str) -> dict:
    token_data = exchange_google_code(code)

    access_token = token_data.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Google authentication failed.",
        )

    response = requests.get(
        GOOGLE_USERINFO_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        timeout=15,
    )

    if not response.ok:
        raise HTTPException(
            status_code=401,
            detail="Unable to retrieve your Google account.",
        )

    user = response.json()

    if not user.get("sub") or not user.get("email"):
        raise HTTPException(
            status_code=401,
            detail="Google account information is incomplete.",
        )

    if not user.get("email_verified"):
        raise HTTPException(
            status_code=401,
            detail="Your Google email is not verified.",
        )

    return user


def authenticate_google_user(
    code: str,
    mode: str = "signin",
) -> dict:
    google_user = get_google_user(code)

    email = google_user["email"].strip().lower()
    google_subject = google_user["sub"]

    existing = get_user_by_email(email)

    if mode == "signup":
        if existing:
            if (
                existing.get("google_subject")
                and existing["google_subject"] != google_subject
            ):
                raise HTTPException(
                    status_code=409,
                    detail="This email is already linked to another Google account.",
                )

            return {
                "status": "account_exists",
                "email": email,
            }

        user = create_user(
            email=email,
            password_hash=None,
            auth_provider="google",
            google_subject=google_subject,
        )
        account_created = True

    else:
        if not existing:
            return {
                "status": "account_not_found",
                "email": email,
            }

        if (
            existing.get("google_subject")
            and existing["google_subject"] != google_subject
        ):
            raise HTTPException(
                status_code=409,
                detail="This email is already linked to another Google account.",
            )

        user = existing
        account_created = False

    token = create_access_token(user["user_id"])

    return {
        "status": "authenticated",
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "auth_provider": user["auth_provider"],
        },
        "access_token": token,
        "token_type": "bearer",
        "account_created": account_created,
    }
