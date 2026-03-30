"""
Users API — User management (owner only) + employee listing for supervisors.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.audit import AuditLog, AuditAction, Notification, NotificationType
from app.schemas import UserResponse, UserCreate, UserUpdate, UserListResponse
from app.core import hash_password
from app.core.rbac import get_current_user, require_role, ALL_PERMISSIONS, ROLE_DEFAULT_PERMISSIONS
from app.core.dependencies import PaginationParams

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=UserListResponse)
async def list_users(
    role: str | None = None,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_role("supervisor", "owner")),
    db: AsyncSession = Depends(get_db),
):
    query = select(User)
    if role:
        query = query.where(User.role == role)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(User.created_at.desc()).offset(pagination.offset).limit(pagination.size)
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=pagination.page,
        size=pagination.size,
    )


@router.get("/employees")
async def list_employees(
    current_user: User = Depends(require_role("supervisor", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Quick list of active employees for assignment dropdowns."""
    result = await db.execute(
        select(User)
        .where(User.role == UserRole.employee, User.is_active == True)
        .order_by(User.name)
    )
    employees = result.scalars().all()
    return [
        {"id": str(u.id), "name": u.name, "phone": u.phone}
        for u in employees
    ]


@router.get("/pending", response_model=UserListResponse)
async def list_pending_partners(
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """List partners awaiting approval (is_active=False)."""
    query = select(User).where(User.role == UserRole.partner, User.is_active == False)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    result = await db.execute(query.order_by(User.created_at.desc()))
    users = result.scalars().all()
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=1,
        size=500,
    )


@router.post("/{user_id}/approve")
async def approve_partner(
    user_id: uuid.UUID,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """Approve a pending partner registration."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "المستخدم غير موجود")
    if user.role != UserRole.partner:
        raise HTTPException(400, "ليس شريكاً")
    if user.is_active:
        raise HTTPException(400, "الحساب مفعّال بالفعل")

    user.is_active = True

    # Notify the partner
    db.add(Notification(
        user_id=user.id,
        notification_type=NotificationType.approval_result,
        title="تم تفعيل حسابك",
        message=f"مرحباً {user.name}! تمت موافقة الإدارة على تسجيلك. يمكنك تسجيل الدخول.",
        is_read=False,
    ))

    db.add(AuditLog(
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role.value,
        action=AuditAction.partner_approved,
        details={"approved_user_id": str(user_id), "name": user.name},
    ))

    await db.commit()
    return {"status": "approved", "name": user.name}


@router.post("/{user_id}/reject")
async def reject_partner(
    user_id: uuid.UUID,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """Reject and delete a pending partner registration."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "المستخدم غير موجود")
    if user.role != UserRole.partner or user.is_active:
        raise HTTPException(400, "لا يمكن رفض هذا الحساب")

    user_name = user.name
    db.add(AuditLog(
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role.value,
        action=AuditAction.partner_rejected,
        details={"rejected_user_id": str(user_id), "name": user_name},
    ))

    # Nullify FK references in audit_log before deleting user (PRAGMA foreign_keys=ON)
    await db.execute(update(AuditLog).where(AuditLog.user_id == user_id).values(user_id=None))

    await db.delete(user)
    await db.commit()
    return {"status": "rejected"}


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreate,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    # Check duplicate
    existing = await db.execute(select(User).where(User.phone == body.phone))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "رقم الجوال مسجّل مسبقاً")

    user = User(
        name=body.name,
        phone=body.phone,
        password_hash=hash_password(body.password),
        role=UserRole(body.role),
    )
    db.add(user)
    await db.flush()

    audit = AuditLog(
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role.value,
        action=AuditAction.user_created,
        details={"new_user_id": str(user.id), "role": body.role},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "المستخدم غير موجود")

    if body.name is not None:
        user.name = body.name
    if body.phone is not None:
        user.phone = body.phone
    if body.role is not None:
        user.role = UserRole(body.role)
    if body.is_active is not None:
        user.is_active = body.is_active

    audit = AuditLog(
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role.value,
        action=AuditAction.user_updated,
        details={"updated_user_id": str(user_id), "changes": body.model_dump(exclude_none=True)},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "المستخدم غير موجود")

    if user.id == current_user.id:
        raise HTTPException(400, "لا يمكنك تعطيل حسابك")

    user.is_active = False

    audit = AuditLog(
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role.value,
        action=AuditAction.user_deactivated,
        details={"deactivated_user_id": str(user_id)},
    )
    db.add(audit)

    await db.commit()
    return {"status": "deactivated"}


# ─── Permissions Endpoints ────────────────────────────

from pydantic import BaseModel as _PermBaseModel

class PermissionsUpdate(_PermBaseModel):
    extra_permissions: list[str]


@router.get("/permissions/definitions")
async def get_permission_definitions(
    current_user: User = Depends(require_role("owner")),
):
    """Return all available permission keys with Arabic labels and role defaults."""
    return {
        "all_permissions": [
            {"key": k, "label": v}
            for k, v in ALL_PERMISSIONS.items()
        ],
        "role_defaults": ROLE_DEFAULT_PERMISSIONS,
    }


@router.get("/{user_id}/permissions")
async def get_user_permissions(
    user_id: uuid.UUID,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """Get current permissions for a user (role defaults + extra granted)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "المستخدم غير موجود")

    role_perms = ROLE_DEFAULT_PERMISSIONS.get(user.role.value, [])
    extra = user.extra_permissions or []
    all_perms = list(set(role_perms) | set(extra))

    return {
        "user_id": str(user.id),
        "user_name": user.name,
        "role": user.role.value,
        "role_permissions": role_perms,
        "extra_permissions": extra,
        "effective_permissions": all_perms,
    }


@router.patch("/{user_id}/permissions")
async def update_user_permissions(
    user_id: uuid.UUID,
    body: PermissionsUpdate,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """Grant or revoke extra permissions for a user (beyond their role defaults)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "المستخدم غير موجود")

    if user.role == UserRole.owner:
        raise HTTPException(400, "المالك لديه جميع الصلاحيات افتراضياً")

    # Validate permission keys
    invalid = [p for p in body.extra_permissions if p not in ALL_PERMISSIONS]
    if invalid:
        raise HTTPException(400, f"صلاحيات غير معروفة: {', '.join(invalid)}")

    old_perms = user.extra_permissions or []
    user.extra_permissions = body.extra_permissions

    db.add(AuditLog(
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role.value,
        action=AuditAction.user_updated,
        details={
            "target_user_id": str(user_id),
            "action": "permissions_updated",
            "old_extra_permissions": old_perms,
            "new_extra_permissions": body.extra_permissions,
        },
    ))

    await db.commit()
    await db.refresh(user)

    return {
        "user_id": str(user.id),
        "user_name": user.name,
        "role": user.role.value,
        "extra_permissions": user.extra_permissions or [],
    }
