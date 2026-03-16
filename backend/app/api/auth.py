"""
Auth API — Login, Register, Refresh, Me, Password Reset (OTP via WhatsApp).
"""

import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.audit import AuditLog, AuditAction, Notification, NotificationType
from app.schemas import (
    LoginRequest, RegisterRequest, TokenResponse,
    RefreshRequest, UserResponse,
)
from app.core import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    login_limiter,
)
from app.core.rbac import get_current_user
from app.services.whatsapp import WhatsAppService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"

    # Rate limit
    if login_limiter.is_blocked(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="تم تجاوز عدد المحاولات المسموح. حاول لاحقاً.",
        )

    # Find user
    result = await db.execute(select(User).where(User.phone == body.phone))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        login_limiter.record(client_ip)

        # Audit failed login
        audit = AuditLog(
            action=AuditAction.login_failed,
            ip_address=client_ip,
            details={"phone": body.phone},
        )
        db.add(audit)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رقم الجوال أو كلمة المرور غير صحيحة",
        )

    if not user.is_active:
        if user.role == UserRole.partner:
            detail = "حسابك في انتظار موافقة الإدارة. سيتم إشعارك عند التفعيل."
        else:
            detail = "الحساب معطّل. تواصل مع الإدارة."
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )

    # Success — reset rate limiter
    login_limiter.reset(client_ip)

    # Generate tokens
    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Audit
    audit = AuditLog(
        user_id=user.id,
        user_name=user.name,
        user_role=user.role.value,
        action=AuditAction.login,
        ip_address=client_ip,
    )
    db.add(audit)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Check duplicate phone
    existing = await db.execute(select(User).where(User.phone == body.phone))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="رقم الجوال مسجّل مسبقاً",
        )

    user = User(
        name=body.name,
        phone=body.phone,
        password_hash=hash_password(body.password),
        role=UserRole.partner,  # Self-registration = partner only
        is_active=False,  # Pending owner approval
    )
    db.add(user)
    await db.flush()

    # Audit
    client_ip = request.client.host if request.client else "unknown"
    audit = AuditLog(
        user_id=user.id,
        user_name=user.name,
        user_role=user.role.value,
        action=AuditAction.register,
        ip_address=client_ip,
    )
    db.add(audit)

    # Notify all active owners
    owners_result = await db.execute(
        select(User).where(User.role == UserRole.owner, User.is_active == True)
    )
    for owner in owners_result.scalars().all():
        db.add(Notification(
            user_id=owner.id,
            notification_type=NotificationType.new_partner,
            title=f"طلب تسجيل جديد: {user.name}",
            message=f"رقم الجوال: {user.phone} — يتطلب موافقتك",
            is_read=False,
        ))

    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    payload = decode_token(body.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(400, "رمز غير صالح للتجديد")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(401, "المستخدم غير موجود أو معطّل")

    token_data = {"sub": str(user.id), "role": user.role.value}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


# ─── Password Reset (OTP via WhatsApp) ─────────────────

OTP_EXPIRATION_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


@router.post("/forgot-password", status_code=200)
async def forgot_password(
    request: Request,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Send OTP to phone. Always returns 200 to prevent user enumeration."""
    phone = body.get("phone", "").strip()
    if not phone:
        # Still return 200 to prevent enumeration
        return {"message": "إذا كان الرقم مسجّلاً، سيتم إرسال رمز تحقق"}

    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        # Generate 4-digit OTP
        otp = f"{random.randint(1000, 9999)}"
        user.otp_code = otp
        user.otp_expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRATION_MINUTES)
        user.otp_attempts = 0
        await db.commit()

        # Send via WhatsApp
        try:
            wa = WhatsAppService()
            await wa.send_text(
                phone,
                f"رمز تحقق جنان بز: {otp}\nصالح لمدة {OTP_EXPIRATION_MINUTES} دقائق.",
            )
        except Exception:
            # If WhatsApp fails, log it but still respond 200
            pass

        # Audit
        client_ip = request.client.host if request.client else "unknown"
        db.add(AuditLog(
            user_id=user.id,
            user_name=user.name,
            user_role=user.role.value,
            action=AuditAction.login,  # reuse login action for audit
            ip_address=client_ip,
            details={"action": "otp_sent", "phone": phone},
        ))
        await db.commit()

    return {"message": "إذا كان الرقم مسجّلاً، سيتم إرسال رمز تحقق"}


@router.post("/verify-otp", status_code=200)
async def verify_otp(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Verify OTP code. Returns a reset_token if valid."""
    phone = body.get("phone", "").strip()
    code = body.get("code", "").strip()

    if not phone or not code:
        raise HTTPException(400, "رقم الجوال والرمز مطلوبان")

    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()

    if not user or not user.otp_code or not user.otp_expires_at:
        raise HTTPException(400, "الرمز غير صحيح أو منتهي الصلاحية")

    # Check attempts
    if user.otp_attempts >= MAX_OTP_ATTEMPTS:
        user.otp_code = None
        user.otp_expires_at = None
        await db.commit()
        raise HTTPException(429, "تم تجاوز عدد المحاولات. أعد طلب رمز جديد.")

    # Check expiry
    if datetime.utcnow() > user.otp_expires_at:
        user.otp_code = None
        user.otp_expires_at = None
        await db.commit()
        raise HTTPException(400, "الرمز منتهي الصلاحية. أعد طلب رمز جديد.")

    # Check code
    if user.otp_code != code:
        user.otp_attempts += 1
        await db.commit()
        raise HTTPException(400, "الرمز غير صحيح")

    # OTP valid — generate a one-time reset token
    reset_token = create_access_token(
        {"sub": str(user.id), "purpose": "reset"},
        expires_delta=timedelta(minutes=15),
    )

    # Clear OTP
    user.otp_code = None
    user.otp_expires_at = None
    user.otp_attempts = 0
    await db.commit()

    return {"reset_token": reset_token}


@router.post("/reset-password", status_code=200)
async def reset_password(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using the reset_token from verify-otp."""
    reset_token = body.get("reset_token", "")
    new_password = body.get("new_password", "")

    if not reset_token or not new_password:
        raise HTTPException(400, "الرمز وكلمة المرور الجديدة مطلوبان")

    if len(new_password) < 6:
        raise HTTPException(400, "كلمة المرور يجب أن تكون 6 أحرف على الأقل")

    # Decode reset token
    try:
        payload = decode_token(reset_token)
    except HTTPException:
        raise HTTPException(400, "رمز إعادة التعيين غير صالح أو منتهي الصلاحية")

    if payload.get("purpose") != "reset":
        raise HTTPException(400, "رمز غير صالح للتعيين")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, "المستخدم غير موجود")

    user.password_hash = hash_password(new_password)
    await db.commit()

    return {"message": "تم تغيير كلمة المرور بنجاح"}


# ─── Change Password (logged-in user) ──────────────────

@router.post("/change-password", status_code=200)
async def change_password(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password for the currently logged-in user."""
    current_password = body.get("current_password", "")
    new_password = body.get("new_password", "")

    if not current_password or not new_password:
        raise HTTPException(400, "كلمة المرور الحالية والجديدة مطلوبتان")

    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(400, "كلمة المرور الحالية غير صحيحة")

    if len(new_password) < 6:
        raise HTTPException(400, "كلمة المرور الجديدة يجب أن تكون 6 أحرف على الأقل")

    current_user.password_hash = hash_password(new_password)
    await db.commit()

    return {"message": "تم تغيير كلمة المرور بنجاح"}
