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


# ─── Granular Permissions System ──────────────────────

# All available permissions with Arabic labels
ALL_PERMISSIONS: dict[str, str] = {
    # ── المستخدمون ──
    "add_users":           "إضافة مستخدمين جدد",
    "edit_users":          "تعديل بيانات المستخدمين",
    "promote_roles":       "ترقية الأدوار (موظف ← مشرف ← مالك)",
    "approve_partners":    "الموافقة على طلبات تسجيل الشركاء ورفضها",
    "manage_permissions":  "إدارة صلاحيات المستخدمين",
    # ── الملفات والطلبات ──
    "view_partner_files":  "الاطلاع على ملفات وطلبات الشركاء",
    "view_employee_files": "الاطلاع على ملفات وأعمال الموظفين",
    "update_case_stages":  "رفع مراحل الملفات (تقديم ← موافقة ← اعتماد...)",
    "assign_cases":        "تعيين الملفات على موظفين",
    "view_all_cases":      "مراجعة جميع الملفات والطلبات",
    # ── الجهات التمويلية ──
    "add_entities":        "إضافة جهات تمويلية جديدة",
    "edit_entities":       "تعديل بيانات الجهات التمويلية",
    # ── موظفو الجهات التمويلية ──
    "view_entity_contacts":   "الاطلاع على موظفي الجهات التمويلية",
    "manage_entity_contacts": "إدارة موظفي الجهات التمويلية",
    # ── سجل الوسطاء ──
    "view_brokers":        "الاطلاع على سجل الوسطاء",
    "manage_brokers":      "إدارة سجل الوسطاء",
    # ── سجل المنشآت ──
    "view_business_registry":   "الاطلاع على سجل المنشآت",
    "manage_business_registry": "إدارة سجل المنشآت",
    # ── التسويق ──
    "send_campaigns":      "إنشاء وإرسال الحملات التسويقية عبر واتساب",
    # ── التقارير ──
    "view_analytics":      "عرض الإحصائيات والتقارير",
    "view_employee_stats": "عرض إحصائيات أداء الموظفين",
    # ── الطلبات (متقدم) ──
    "delete_cases":        "حذف الطلبات نهائياً",
    "create_cases":        "رفع طلبات تحليل جديدة (للموظفين)",
}

# Default permissions per role
ROLE_DEFAULT_PERMISSIONS: dict[str, list[str]] = {
    "partner":    [],
    "employee":   [
        "view_partner_files",
        "update_case_stages",
    ],
    "supervisor": [
        "add_users",
        "edit_users",
        "approve_partners",
        "view_partner_files",
        "view_employee_files",
        "update_case_stages",
        "assign_cases",
        "view_all_cases",
        "view_analytics",
    ],
    "owner": list(ALL_PERMISSIONS.keys()),  # owner always has everything
}


def has_permission(user: "User", permission: str) -> bool:
    """Check if user has a specific permission (role default OR extra grant)."""
    if user.role == UserRole.owner:
        return True
    role_perms = ROLE_DEFAULT_PERMISSIONS.get(user.role.value, [])
    extra = user.extra_permissions or []
    return permission in role_perms or permission in extra


def require_permission(permission: str) -> Callable:
    """
    Dependency factory — require a named permission.
    Checks both role defaults and extra_permissions granted by owner.

    Usage:
        @router.post("/", dependencies=[Depends(require_permission("manage_users"))])
    """
    async def _check(user: User = Depends(get_current_user)):
        if not has_permission(user, permission):
            label = ALL_PERMISSIONS.get(permission, permission)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"ليس لديك صلاحية: {label}",
            )
        return user
    return _check


# ─── Fine-grained permission checks (helpers) ──────────

def can_see_entity_names(user: User) -> bool:
    return user.role in (UserRole.owner, UserRole.employee, UserRole.supervisor)


def can_advance_stage(user: User) -> bool:
    return user.role in (UserRole.employee, UserRole.supervisor, UserRole.owner) or has_permission(user, 'update_case_stages')


def can_approve_transitions(user: User) -> bool:
    return user.role in (UserRole.supervisor, UserRole.owner) or has_permission(user, 'update_case_stages')


def can_reject_case(user: User) -> bool:
    return user.role in (UserRole.supervisor, UserRole.owner) or has_permission(user, 'update_case_stages')


def can_assign_cases(user: User) -> bool:
    return user.role in (UserRole.supervisor, UserRole.owner) or has_permission(user, 'assign_cases')


def can_request_completion(user: User) -> bool:
    return user.role in (UserRole.employee, UserRole.supervisor, UserRole.owner)


def can_see_audit_log(user: User) -> bool:
    return user.role in (UserRole.supervisor, UserRole.owner)


def can_manage_entity_rules(user: User) -> bool:
    return user.role == UserRole.owner

def can_delete_cases(user: "User") -> bool:
    return user.role == UserRole.owner or has_permission(user, 'delete_cases')


def can_create_cases(user: "User") -> bool:
    return user.role in (UserRole.partner, UserRole.owner) or has_permission(user, 'create_cases')

def can_manage_users(user: User) -> bool:
    return user.role == UserRole.owner
