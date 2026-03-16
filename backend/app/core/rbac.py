"""
RBAC — Role-Based Access Control dependencies for FastAPI.

Usage in routes:
    @router.get("/admin-stuff", dependencies=[Depends(require_role("owner"))])
    async def admin_only(current_user: User = Depends(get_current_user)):
        ...
"""

from typing import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.core import decode_token, oauth2_scheme


# ─── Get current user from JWT ──────────────────────────

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)  # raises 401 on invalid
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="رمز غير صالح")

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="المستخدم غير موجود أو معطّل")

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_active:
        raise HTTPException(status_code=403, detail="الحساب معطّل")
    return user


# ─── Role requirements ──────────────────────────────────

def require_role(*roles: str) -> Callable:
    """
    Dependency factory — call with allowed role names.

    Usage:
        @router.get("/", dependencies=[Depends(require_role("supervisor", "owner"))])
    """
    async def _check(user: User = Depends(get_current_user)):
        if user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ليس لديك صلاحية للوصول إلى هذا المورد",
            )
        return user
    return _check


def require_any_staff() -> Callable:
    """Require employee, supervisor, or owner."""
    return require_role("employee", "supervisor", "owner")


def require_supervisor_or_owner() -> Callable:
    """Require supervisor or owner."""
    return require_role("supervisor", "owner")


def require_owner() -> Callable:
    """Require owner only."""
    return require_role("owner")


# ─── Fine-grained permission checks (helpers) ──────────

def can_see_entity_names(user: User) -> bool:
    return user.role in (UserRole.owner, UserRole.employee, UserRole.supervisor)


def can_advance_stage(user: User) -> bool:
    return user.role in (UserRole.employee, UserRole.supervisor, UserRole.owner)


def can_approve_transitions(user: User) -> bool:
    return user.role in (UserRole.supervisor, UserRole.owner)


def can_reject_case(user: User) -> bool:
    return user.role in (UserRole.supervisor, UserRole.owner)


def can_assign_cases(user: User) -> bool:
    return user.role in (UserRole.supervisor, UserRole.owner)


def can_request_completion(user: User) -> bool:
    return user.role in (UserRole.employee, UserRole.supervisor, UserRole.owner)


def can_see_audit_log(user: User) -> bool:
    return user.role in (UserRole.supervisor, UserRole.owner)


def can_manage_entity_rules(user: User) -> bool:
    return user.role == UserRole.owner


def can_manage_users(user: User) -> bool:
    return user.role == UserRole.owner
