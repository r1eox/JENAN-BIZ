"""
Entity Contact — employees/representatives at funding entities.
Linked to EntityRule by entity_code.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.compat import GUID
from app.database import Base


class EntityContact(Base):
    """Contacts (employees/reps) at funding entities."""

    __tablename__ = "entity_contacts"
    __table_args__ = (
        Index("ix_entity_contacts_entity_code", "entity_code"),
        Index("ix_entity_contacts_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    entity_code: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(200), default="")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[str] = mapped_column(String(200), default="")   # المنصب
    phone: Mapped[str] = mapped_column(String(20), default="")
    email: Mapped[str] = mapped_column(String(200), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
