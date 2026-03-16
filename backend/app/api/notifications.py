"""
Notifications API — In-app notifications + WhatsApp auto-notifications.
Endpoints:
  GET  /notifications/         → list user's notifications (paginated)
  GET  /notifications/unread   → unread count
  POST /notifications/{id}/read → mark as read
  POST /notifications/read-all → mark all as read
  POST /notifications/send-whatsapp/{case_id} → send WhatsApp reminder for missing docs
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.audit import Notification, NotificationType
from app.models.case import Case
from app.core.rbac import get_current_user, require_role
from app.core.dependencies import PaginationParams
from app.services.whatsapp import get_whatsapp

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ─── Schemas ────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: uuid.UUID
    notification_type: str
    title: str
    message: str
    case_id: uuid.UUID | None = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationOut]
    total: int
    unread: int
    page: int
    size: int


class UnreadCountResponse(BaseModel):
    unread: int


class WhatsAppReminderRequest(BaseModel):
    phone: str = ""  # override recipient phone (optional)
    custom_message: str = ""  # override default message


class BulkNotifyRequest(BaseModel):
    """Send auto-notification to all cases with missing documents."""
    pass


# ─── Endpoints ──────────────────────────────────────────

@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's notifications (newest first)."""
    base = select(Notification).where(Notification.user_id == current_user.id)

    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar() or 0

    unread = (await db.execute(
        select(func.count()).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )).scalar() or 0

    q = base.order_by(Notification.created_at.desc()).offset(pagination.offset).limit(pagination.size)
    rows = (await db.execute(q)).scalars().all()

    return NotificationListResponse(
        items=[NotificationOut.model_validate(n) for n in rows],
        total=total,
        unread=unread,
        page=pagination.page,
        size=pagination.size,
    )


@router.get("/unread", response_model=UnreadCountResponse)
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Quick unread count for notification bell badge."""
    count = (await db.execute(
        select(func.count()).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )).scalar() or 0
    return UnreadCountResponse(unread=count)


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(404, "الإشعار غير موجود")
    notif.is_read = True
    await db.commit()
    return {"status": "ok"}


@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return {"status": "ok"}


@router.post("/send-whatsapp/{case_id}")
async def send_whatsapp_reminder(
    case_id: uuid.UUID,
    body: WhatsAppReminderRequest | None = None,
    current_user: User = Depends(require_role("employee", "supervisor", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """
    Send WhatsApp reminder to the partner about a specific case.
    Typically used to notify about missing documents or needed actions.
    """
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    # Get the partner who owns the case
    partner_result = await db.execute(select(User).where(User.id == case.partner_id))
    partner = partner_result.scalar_one_or_none()
    if not partner:
        raise HTTPException(404, "الشريك غير موجود")

    phone = (body.phone if body and body.phone else partner.phone) or ""
    if not phone:
        raise HTTPException(400, "لا يوجد رقم جوال للمستلم")

    # Build the message
    if body and body.custom_message:
        message = body.custom_message
    else:
        message = (
            f"🔔 تنبيه من جنان بز\n\n"
            f"مرحباً {partner.name}،\n"
            f"يرجى مراجعة طلبك رقم {str(case.id)[:8]} — "
            f"هناك مستندات ناقصة أو تحتاج إلى تحديث.\n\n"
            f"يرجى تسجيل الدخول إلى المنصة لاستكمال المطلوب.\n"
            f"فريق جنان بز"
        )

    wa = get_whatsapp()
    success = await wa.send_text(phone, message)

    # Create in-app notification too
    notif = Notification(
        user_id=partner.id,
        notification_type=NotificationType.general,
        title="تنبيه: مستندات ناقصة",
        message=message,
        case_id=case.id,
    )
    db.add(notif)
    await db.commit()

    return {
        "status": "sent" if success else "failed",
        "phone": phone,
        "whatsapp_sent": success,
    }


@router.post("/auto-remind-missing-docs")
async def auto_remind_missing_docs(
    current_user: User = Depends(require_role("supervisor", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """
    Auto-send WhatsApp reminders to ALL partners whose cases are
    in 'تحميل المستندات' or 'تقييم الأهلية' stages and have been
    pending for more than 2 days.
    """
    from datetime import timedelta

    cutoff = datetime.utcnow() - timedelta(days=2)

    # Find stale cases in upload/eligibility stages
    result = await db.execute(
        select(Case, User)
        .join(User, Case.partner_id == User.id)
        .where(
            Case.current_stage.in_(["تحميل المستندات", "تقييم الأهلية"]),
            Case.updated_at < cutoff,
        )
    )
    rows = result.all()

    wa = get_whatsapp()
    sent = 0
    failed = 0

    for case, partner in rows:
        message = (
            f"🔔 تذكير من جنان بز\n\n"
            f"مرحباً {partner.name}،\n"
            f"طلبك رقم {str(case.id)[:8]} في مرحلة «{case.current_stage}» "
            f"منذ أكثر من يومين.\n"
            f"يرجى استكمال المطلوب في أقرب وقت.\n\n"
            f"فريق جنان بز"
        )

        success = await wa.send_text(partner.phone, message)
        if success:
            sent += 1
        else:
            failed += 1

        # In-app notification
        notif = Notification(
            user_id=partner.id,
            notification_type=NotificationType.general,
            title="تذكير: يرجى استكمال الطلب",
            message=message,
            case_id=case.id,
        )
        db.add(notif)

    await db.commit()
    return {"total": len(rows), "sent": sent, "failed": failed}
