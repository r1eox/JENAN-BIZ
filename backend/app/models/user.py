"""
Jenan BIZ — User Model
Roles: partner, employee, supervisor, owner
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.compat import GUID, JSONType

from app.database import Base


class UserRole(str, enum.Enum):
    partner = "partner"
    employee = "employee"
    supervisor = "supervisor"
    owner = "owner"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role_enum"), nullable=False, default=UserRole.partner
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Extra permissions beyond the role's defaults (owner can grant these)
    extra_permissions: Mapped[list] = mapped_column(JSONType, default=list, nullable=False, server_default="[]")

    # OTP for password reset
    otp_code: Mapped[str | None] = mapped_column(String(6), nullable=True, default=None)
    otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    otp_attempts: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<User {self.name} ({self.role.value})>"
