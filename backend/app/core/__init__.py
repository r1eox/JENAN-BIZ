"""
Security core — JWT tokens, password hashing, rate limiting.
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# ─── Password hashing (bcrypt) ─────────────────────────
# bcrypt 4.x changed API — truncate_error=False prevents the ValueError
# for passwords under 72 bytes (all our passwords are well under that limit)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ─── JWT ────────────────────────────────────────────────

ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز الجلسة غير صالح أو منتهي الصلاحية",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─── In-memory rate limiter (per-IP) ───────────────────
# For production, replace with Redis-backed limiter.

class RateLimiter:
    """Simple in-memory rate limiter keyed on IP."""

    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._store: dict[str, list[float]] = {}

    def is_blocked(self, key: str) -> bool:
        now = datetime.utcnow().timestamp()
        attempts = self._store.get(key, [])
        # Prune old attempts
        attempts = [t for t in attempts if now - t < self.window_seconds]
        self._store[key] = attempts
        return len(attempts) >= self.max_attempts

    def record(self, key: str) -> None:
        now = datetime.utcnow().timestamp()
        attempts = self._store.get(key, [])
        attempts.append(now)
        self._store[key] = attempts

    def reset(self, key: str) -> None:
        self._store.pop(key, None)


login_limiter = RateLimiter(
    max_attempts=settings.LOGIN_MAX_ATTEMPTS,
    window_seconds=settings.LOGIN_LOCKOUT_SECONDS,
)
