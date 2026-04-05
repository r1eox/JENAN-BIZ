"""
Broker — intermediary/broker registry.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.compat import GUID
from app.database import Base


class Broker(Base):
    """Broker/intermediary registry."""

    __tablename__ = "brokers"
    __table_args__ = (
        Index("ix_brokers_phone", "phone"),
        Index("ix_brokers_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), default="")
    email: Mapped[str] = mapped_column(String(200), default="")
    company_name: Mapped[str] = mapped_column(String(300), default="")
    cr_number: Mapped[str] = mapped_column(String(50), default="")     # رقم السجل التجاري
    city: Mapped[str] = mapped_column(String(100), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
