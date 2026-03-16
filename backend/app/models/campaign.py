"""
Marketing campaign model — Owner sends WhatsApp campaigns to groups.
"""

import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.compat import GUID, JSONType

from app.database import Base


class CampaignStatus(str, Enum):
    draft = "draft"
    sending = "sending"
    sent = "sent"
    failed = "failed"
    cancelled = "cancelled"


class ContentType(str, Enum):
    text = "text"
    image = "image"
    video = "video"
    document = "document"


class TargetAudience(str, Enum):
    all_users = "all_users"  # كل المستخدمين المسجلين
    partners = "partners"  # الشركاء فقط
    employees = "employees"  # الموظفين فقط
    external = "external"  # جهات خارجية فقط
    custom_group = "custom_group"  # مجموعة مخصصة من جهات الاتصال
    all = "all"  # الكل (مسجلين + خارجيين)


class Campaign(Base):
    """
    WhatsApp marketing campaign.
    """

    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content_type: Mapped[ContentType] = mapped_column(
        SAEnum(ContentType), default=ContentType.text
    )
    content_text: Mapped[str] = mapped_column(Text, default="")
    media_url: Mapped[str] = mapped_column(String(500), default="")  # image/video/doc URL
    media_caption: Mapped[str] = mapped_column(Text, default="")

    target_audience: Mapped[TargetAudience] = mapped_column(
        SAEnum(TargetAudience), default=TargetAudience.all
    )
    target_group: Mapped[str] = mapped_column(
        String(100), default=""
    )  # if custom_group, which group

    status: Mapped[CampaignStatus] = mapped_column(
        SAEnum(CampaignStatus), default=CampaignStatus.draft
    )
    total_recipients: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[list | None] = mapped_column(JSONType(), nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
