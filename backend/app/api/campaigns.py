"""
Marketing Campaigns API — Owner creates and sends WhatsApp campaigns.
Endpoints:
  GET    /campaigns/         → list campaigns (paginated)
  POST   /campaigns/         → create campaign (draft)
  GET    /campaigns/{id}     → campaign detail
  PATCH  /campaigns/{id}     → update draft campaign
  DELETE /campaigns/{id}     → delete draft campaign
  POST   /campaigns/{id}/send → send campaign via WhatsApp
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from loguru import logger

from app.database import get_db, async_session
from app.models.user import User, UserRole
from app.models.contact import Contact
from app.models.campaign import (
    Campaign, CampaignStatus, ContentType, TargetAudience,
)
from app.core.rbac import require_role
from app.core.dependencies import PaginationParams
from app.services.whatsapp import get_whatsapp

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


# ─── Schemas ────────────────────────────────────────────

class CampaignCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=300)
    content_type: str = "text"  # text | image | video | document
    content_text: str = ""
    media_url: str = ""
    media_caption: str = ""
    target_audience: str = "all"  # all_users | partners | employees | external | custom_group | all
    target_group: str = ""  # group name if custom_group


class CampaignUpdate(BaseModel):
    title: str | None = None
    content_type: str | None = None
    content_text: str | None = None
    media_url: str | None = None
    media_caption: str | None = None
    target_audience: str | None = None
    target_group: str | None = None


class CampaignOut(BaseModel):
    id: uuid.UUID
    title: str
    content_type: str
    content_text: str
    media_url: str
    media_caption: str
    target_audience: str
    target_group: str
    status: str
    total_recipients: int
    sent_count: int
    failed_count: int
    error_log: list | None = None
    sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CampaignListResponse(BaseModel):
    items: list[CampaignOut]
    total: int
    page: int
    size: int


# ─── Helpers ────────────────────────────────────────────

async def _gather_recipients(
    target_audience: TargetAudience,
    target_group: str,
    db: AsyncSession,
) -> list[str]:
    """Gather phone numbers based on target audience."""
    phones: list[str] = []

    if target_audience in (TargetAudience.all_users, TargetAudience.all, TargetAudience.partners):
        q = select(User.phone).where(User.is_active == True)
        if target_audience == TargetAudience.partners:
            q = q.where(User.role == UserRole.partner)
        rows = (await db.execute(q)).all()
        phones.extend([r[0] for r in rows if r[0]])

    if target_audience in (TargetAudience.employees,):
        rows = (await db.execute(
            select(User.phone).where(User.is_active == True, User.role == UserRole.employee)
        )).all()
        phones.extend([r[0] for r in rows if r[0]])

    if target_audience in (TargetAudience.external, TargetAudience.all):
        q = select(Contact.phone).where(Contact.is_active == True)
        rows = (await db.execute(q)).all()
        phones.extend([r[0] for r in rows if r[0]])

    if target_audience == TargetAudience.custom_group and target_group:
        rows = (await db.execute(
            select(Contact.phone).where(
                Contact.is_active == True,
                Contact.group_name == target_group,
            )
        )).all()
        phones.extend([r[0] for r in rows if r[0]])

    # De-duplicate
    return list(set(phones))


async def _execute_campaign(campaign_id: uuid.UUID):
    """Background task: send WhatsApp messages for a campaign."""
    async with async_session() as db:
        result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
        campaign = result.scalar_one_or_none()
        if not campaign:
            return

        try:
            phones = await _gather_recipients(
                campaign.target_audience, campaign.target_group, db
            )

            campaign.total_recipients = len(phones)
            campaign.status = CampaignStatus.sending
            await db.commit()

            wa = get_whatsapp()
            sent = 0
            failed = 0
            errors: list[str] = []

            content_type = campaign.content_type

            for phone in phones:
                try:
                    if content_type == ContentType.text:
                        ok = await wa.send_text(phone, campaign.content_text)
                    elif content_type == ContentType.image:
                        ok = await wa.send_image(
                            phone, campaign.media_url, campaign.media_caption or campaign.content_text
                        )
                    elif content_type == ContentType.video:
                        ok = await wa.send_video(
                            phone, campaign.media_url, campaign.media_caption or campaign.content_text
                        )
                    elif content_type == ContentType.document:
                        ok = await wa.send_document(
                            phone, campaign.media_url, campaign.media_caption or "مستند"
                        )
                    else:
                        ok = await wa.send_text(phone, campaign.content_text)

                    if ok and ok.get('success'):
                        sent += 1
                    else:
                        failed += 1
                        errors.append(f"{phone}: {ok.get('error', 'فشل الإرسال')}")
                except Exception as e:
                    failed += 1
                    errors.append(f"{phone}: {str(e)}")

            campaign.sent_count = sent
            campaign.failed_count = failed
            campaign.error_log = errors if errors else None
            campaign.status = CampaignStatus.sent
            campaign.sent_at = datetime.utcnow()
            await db.commit()

            logger.info(
                f"Campaign {campaign_id} completed: {sent} sent, {failed} failed"
            )

        except Exception as e:
            logger.error(f"Campaign {campaign_id} error: {e}")
            campaign.status = CampaignStatus.failed
            campaign.error_log = [str(e)]
            await db.commit()


# ─── Endpoints ──────────────────────────────────────────

@router.get("/", response_model=CampaignListResponse)
async def list_campaigns(
    status: str | None = None,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    base = select(Campaign)
    if status:
        base = base.where(Campaign.status == status)

    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar() or 0

    q = base.order_by(Campaign.created_at.desc()).offset(pagination.offset).limit(pagination.size)
    rows = (await db.execute(q)).scalars().all()

    return CampaignListResponse(
        items=[CampaignOut.model_validate(c) for c in rows],
        total=total,
        page=pagination.page,
        size=pagination.size,
    )


@router.post("/", response_model=CampaignOut, status_code=201)
async def create_campaign(
    body: CampaignCreate,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    campaign = Campaign(
        title=body.title,
        content_type=ContentType(body.content_type),
        content_text=body.content_text,
        media_url=body.media_url,
        media_caption=body.media_caption,
        target_audience=TargetAudience(body.target_audience),
        target_group=body.target_group,
        status=CampaignStatus.draft,
        created_by=current_user.id,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return CampaignOut.model_validate(campaign)


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(404, "الحملة غير موجودة")
    return CampaignOut.model_validate(campaign)


@router.patch("/{campaign_id}", response_model=CampaignOut)
async def update_campaign(
    campaign_id: uuid.UUID,
    body: CampaignUpdate,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(404, "الحملة غير موجودة")

    if campaign.status != CampaignStatus.draft:
        raise HTTPException(400, "لا يمكن تعديل حملة تم إرسالها")

    if body.title is not None:
        campaign.title = body.title
    if body.content_type is not None:
        campaign.content_type = ContentType(body.content_type)
    if body.content_text is not None:
        campaign.content_text = body.content_text
    if body.media_url is not None:
        campaign.media_url = body.media_url
    if body.media_caption is not None:
        campaign.media_caption = body.media_caption
    if body.target_audience is not None:
        campaign.target_audience = TargetAudience(body.target_audience)
    if body.target_group is not None:
        campaign.target_group = body.target_group

    await db.commit()
    await db.refresh(campaign)
    return CampaignOut.model_validate(campaign)


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(404, "الحملة غير موجودة")

    if campaign.status == CampaignStatus.sending:
        raise HTTPException(400, "لا يمكن حذف حملة قيد الإرسال")

    await db.delete(campaign)
    await db.commit()
    return {"status": "deleted"}


@router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """
    Launch campaign sending in background.
    Returns immediately while messages are dispatched.
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(404, "الحملة غير موجودة")

    if campaign.status != CampaignStatus.draft:
        raise HTTPException(400, "يمكن إرسال الحملات المسودة فقط")

    # Validate there's content to send
    if campaign.content_type == ContentType.text and not campaign.content_text:
        raise HTTPException(400, "الحملة النصية بحاجة إلى نص محتوى")
    if campaign.content_type in (ContentType.image, ContentType.video, ContentType.document):
        if not campaign.media_url:
            raise HTTPException(400, "الحملة بحاجة إلى رابط الملف")

    # Count recipients first
    phones = await _gather_recipients(
        campaign.target_audience, campaign.target_group, db
    )
    if not phones:
        raise HTTPException(400, "لا يوجد مستلمون للحملة")

    campaign.total_recipients = len(phones)
    await db.commit()

    # Launch in background
    background_tasks.add_task(_execute_campaign, campaign_id)

    return {
        "status": "sending",
        "total_recipients": len(phones),
        "message": f"جاري إرسال الحملة إلى {len(phones)} مستلم",
    }
