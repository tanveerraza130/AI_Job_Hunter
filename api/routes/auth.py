"""
Authentication API routes.
"""

from typing import Annotated
from urllib.parse import urlencode
import secrets
from datetime import datetime, timedelta, timezone
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Request, status
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
from api.oauth_transactions import (
    create_oauth_state,
    consume_oauth_state,
    create_authorization_code,
    consume_authorization_code,
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



OAUTH_STATE_COOKIE = "ai_job_hunter_oauth_state"
OAUTH_STATE_COOKIE_PATH = "/api/v1/auth/google"


class GoogleCodeExchangeRequest(BaseModel):
    code: str = Field(min_length=20, max_length=200)
    state: str = Field(min_length=20, max_length=200)


def _oauth_cookie_secure() -> bool:
    return bool(
        settings.google_redirect_uri
        and settings.google_redirect_uri.lower().startswith("https://")
    )


def _clear_oauth_cookie(response: RedirectResponse) -> RedirectResponse:
    response.delete_cookie(
        key=OAUTH_STATE_COOKIE,
        path=OAUTH_STATE_COOKIE_PATH,
        secure=_oauth_cookie_secure(),
        httponly=True,
        samesite="lax",
    )
    return response


def _frontend_redirect(path: str, params: dict) -> RedirectResponse:
    url = f"{settings.frontend_url.rstrip('/')}{path}?{urlencode(params)}"
    return RedirectResponse(url=url, status_code=302)


@router.get("/google/start")
async def google_start(mode: str = "signin"):
    if not _google_oauth_configured():
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is not configured.",
        )

    if mode not in {"signin", "signup"}:
        raise HTTPException(status_code=400, detail="Invalid Google login mode.")

    state = secrets.token_urlsafe(32)
    create_oauth_state(state, mode)

    response = RedirectResponse(
        url=get_google_login_url(mode, state),
        status_code=302,
    )
    response.set_cookie(
        key=OAUTH_STATE_COOKIE,
        value=state,
        max_age=600,
        httponly=True,
        secure=_oauth_cookie_secure(),
        samesite="lax",
        path=OAUTH_STATE_COOKIE_PATH,
    )
    return response


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str,
    state: str | None = None,
):
    if not _google_oauth_configured():
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is not configured.",
        )

    cookie_state = request.cookies.get(OAUTH_STATE_COOKIE)
    if (
        not state
        or not cookie_state
        or not secrets.compare_digest(state, cookie_state)
    ):
        raise HTTPException(status_code=400, detail="Invalid OAuth state.")

    mode = consume_oauth_state(state)
    if mode is None:
        raise HTTPException(
            status_code=400,
            detail="OAuth state is invalid, expired, or already used.",
        )

    result = authenticate_google_user(code, mode=mode)

    if result.get("status") == "account_not_found":
        response = _frontend_redirect(
            "/signup",
            {
                "google_error": "account_not_found",
                "email": result["email"],
            },
        )
        return _clear_oauth_cookie(response)

    if result.get("status") == "account_exists":
        response = _frontend_redirect(
            "/signup",
            {
                "google_error": "account_exists",
                "email": result["email"],
            },
        )
        return _clear_oauth_cookie(response)

    profile = get_profile(result["user"]["user_id"])
    profile_complete = profile is not None

    authorization_code = secrets.token_urlsafe(32)
    create_authorization_code(
        authorization_code,
        state,
        {
            "user_id": result["user"]["user_id"],
            "user": result["user"],
            "account_created": bool(result.get("account_created")),
            "profile_complete": profile_complete,
        },
    )

    if mode == "signup" and result.get("account_created"):
        path = "/signup"
        params = {
            "google_success": "1",
            "account_created": "1",
            "code": authorization_code,
            "state": state,
            "email": result["user"]["email"],
        }
    elif profile_complete:
        path = "/dashboard"
        params = {
            "google_success": "1",
            "code": authorization_code,
            "state": state,
        }
    else:
        path = "/login"
        params = {
            "google_success": "1",
            "profile_complete": "0",
            "code": authorization_code,
            "state": state,
            "email": result["user"]["email"],
        }

    response = _frontend_redirect(path, params)
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/google/exchange")
async def google_exchange(
    payload: GoogleCodeExchangeRequest,
    request: Request,
):
    cookie_state = request.cookies.get(OAUTH_STATE_COOKIE)
    if (
        not cookie_state
        or not secrets.compare_digest(payload.state, cookie_state)
    ):
        raise HTTPException(status_code=400, detail="Invalid OAuth exchange.")

    result = consume_authorization_code(payload.code, payload.state)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Authorization code is invalid, expired, or already used.",
        )

    access_token = create_access_token(result["user_id"])

    response = {
        "access_token": access_token,
        "token_type": "bearer",
        "user": result["user"],
        "account_created": result["account_created"],
        "profile_complete": result["profile_complete"],
    }

    from fastapi.responses import JSONResponse

    json_response = JSONResponse(content=response)
    json_response.headers["Cache-Control"] = "no-store"
    json_response.headers["Pragma"] = "no-cache"
    json_response.delete_cookie(
        key=OAUTH_STATE_COOKIE,
        path=OAUTH_STATE_COOKIE_PATH,
        secure=_oauth_cookie_secure(),
        httponly=True,
        samesite="lax",
    )
    return json_response


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
