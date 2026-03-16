"""
External Contact — for marketing campaigns.
Not limited to registered users — Owner can import any phone list.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.compat import GUID, JSONType

from app.database import Base


class Contact(Base):
    """
    External contact for marketing/WhatsApp campaigns.
    Separate from User — these can be anyone (leads, clients, etc.).
    """

    __tablename__ = "contacts"
    __table_args__ = (
        Index("ix_contacts_phone", "phone", unique=True),
        Index("ix_contacts_group", "group_name"),
        Index("ix_contacts_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), default="")
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(300), default="")
    group_name: Mapped[str] = mapped_column(String(100), default="عام")  # for segmentation
    notes: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list | None] = mapped_column(JSONType(), nullable=True)  # ["شريك", "عميل VIP"]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str] = mapped_column(String(50), default="manual")  # manual, import, signup

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
