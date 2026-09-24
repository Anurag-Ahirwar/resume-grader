# backend/app/auth.py
"""Authentication & authorization: password hashing, JWT issuing/verification,
and FastAPI dependencies for protecting routes.

Session mechanism: stateless JWT bearer tokens (see V3 execution plan design notes).
Logout is a client-side token discard -- there is no server-side revocation list,
which is an intentional simplification for a single-tenant local app.
"""
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.db import SessionLocal
from backend.app import models

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours

SESSION_SECRET = os.environ.get("SESSION_SECRET")
if not SESSION_SECRET:
    SESSION_SECRET = secrets.token_hex(32)
    print(
        "WARNING: SESSION_SECRET is not set. Generated a random one for this process only -- "
        "all sessions will be invalidated on restart. Set SESSION_SECRET in your environment "
        "for anything beyond local development."
    )


class Role:
    ADMIN = "admin"
    RECRUITER = "recruiter"
    STUDENT = "student"

    ALL = (ADMIN, RECRUITER, STUDENT)


# ---------------------------------------------------
# Password hashing
# ---------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed hash -- never let this crash the request, just fail closed.
        return False


# ---------------------------------------------------
# JWT
# ---------------------------------------------------

def create_access_token(user: "models.User") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SESSION_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError (or a subclass) on any invalid/expired/malformed token."""
    return jwt.decode(token, SESSION_SECRET, algorithms=[ALGORITHM])


# ---------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> "models.User":
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise unauthorized

    user_id = payload.get("sub")
    if not user_id:
        raise unauthorized

    db = SessionLocal()
    try:
        user = db.query(models.User).filter_by(id=user_id).first()
    finally:
        db.close()

    if user is None or not user.is_active:
        raise unauthorized

    return user


def require_role(*roles: str):
    """Dependency factory: `Depends(require_role(Role.ADMIN))` etc.
    401 if unauthenticated, 403 if authenticated but not one of `roles`."""

    def _check(current_user: "models.User" = Depends(get_current_user)) -> "models.User":
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return _check
