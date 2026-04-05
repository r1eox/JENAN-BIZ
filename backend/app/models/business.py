"""
Business Registry — establishment records (separate from cases/partners).
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.compat import GUID
from app.database import Base


class Business(Base):
    """Business/establishment registry."""

    __tablename__ = "businesses"
    __table_args__ = (
        Index("ix_businesses_cr", "cr_number"),
        Index("ix_businesses_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str] = mapped_column(String(300), nullable=False)
    cr_number: Mapped[str] = mapped_column(String(50), default="")     # رقم السجل
    activity: Mapped[str] = mapped_column(String(200), default="")     # النشاط
    owner_name: Mapped[str] = mapped_column(String(200), default="")
    phone: Mapped[str] = mapped_column(String(20), default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    establishment_year: Mapped[str] = mapped_column(String(10), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
