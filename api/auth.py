"""
Authentication helpers for AI Job Hunter.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from pwdlib import PasswordHash

from api.account_store import create_user, get_user_by_email, get_user_by_id
from api.config import settings


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )

    payload = {
        "sub": user_id,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = payload.get("sub")

        if not user_id:
            raise ValueError("Missing user ID")

        return str(user_id)

    except (jwt.InvalidTokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        ) from exc


def register_email_user(
    email: str,
    password: str,
) -> dict:
    email = email.strip().lower()

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required.",
        )

    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters.",
        )

    existing = get_user_by_email(email)

    if existing:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists. Please log in instead.",
        )

    user = create_user(
        email=email,
        password_hash=hash_password(password),
        auth_provider="email",
    )

    token = create_access_token(user["user_id"])

    return {
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "auth_provider": user["auth_provider"],
        },
        "access_token": token,
        "token_type": "bearer",
        "profile_complete": False,
    }


def login_email_user(
    email: str,
    password: str,
) -> dict:
    email = email.strip().lower()

    user = get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="No account found with this email. Please create an account first.",
        )

    if not user.get("password_hash"):
        raise HTTPException(
            status_code=400,
            detail="This account uses Google sign-in. Please continue with Google.",
        )

    if not verify_password(
        password,
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    token = create_access_token(user["user_id"])

    return {
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "auth_provider": user["auth_provider"],
        },
        "access_token": token,
        "token_type": "bearer",
    }


def get_authenticated_user(
    token: str,
) -> dict:
    user_id = decode_access_token(token)

    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User account not found.",
        )

    return user
