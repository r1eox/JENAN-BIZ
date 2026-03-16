"""
Audit Log and Notification models.

AuditLog — immutable log of every significant action (create, update, stage transition,
login, delete, file upload, approval, assignment, etc.).

Notification — per-user notifications (stage transitions, assignments, approvals).
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.compat import GUID, JSONType

from app.database import Base


class AuditAction(str, enum.Enum):
    # Auth
    login = "login"
    login_failed = "login_failed"
    logout = "logout"
    register = "register"

    # Case lifecycle
    case_created = "case_created"
    case_updated = "case_updated"
    case_stage_changed = "case_stage_changed"
    case_rejected = "case_rejected"
    case_deleted = "case_deleted"

    # Files
    file_uploaded = "file_uploaded"
    analysis_started = "analysis_started"
    analysis_completed = "analysis_completed"
    analysis_failed = "analysis_failed"

    # Assignment
    case_assigned = "case_assigned"
    case_claimed = "case_claimed"

    # Approvals
    approval_requested = "approval_requested"
    approval_granted = "approval_granted"
    approval_denied = "approval_denied"

    # Completion
    completion_requested = "completion_requested"
    note_added = "note_added"

    # User management
    user_created = "user_created"
    user_updated = "user_updated"
    user_deactivated = "user_deactivated"
    partner_approved = "partner_approved"
    partner_rejected = "partner_rejected"

    # Entity rules
    entity_rule_created = "entity_rule_created"
    entity_rule_updated = "entity_rule_updated"
    entity_rules_reordered = "entity_rules_reordered"

    # Owner override
    decision_overridden = "decision_overridden"
    referred_to_review = "referred_to_review"

    # Risk flags
    risk_flags_generated = "risk_flags_generated"

    # File access
    file_downloaded = "file_downloaded"
    file_access_denied = "file_access_denied"


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_user", "user_id"),
        Index("ix_audit_action", "action"),
        Index("ix_audit_case", "case_id"),
        Index("ix_audit_ts", "timestamp"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True
    )
    user_name: Mapped[str] = mapped_column(String(200), default="system")
    user_role: Mapped[str] = mapped_column(String(20), default="system")
    action: Mapped[AuditAction] = mapped_column(
        SAEnum(AuditAction, name="audit_action_enum"), nullable=False
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True
    )
    ip_address: Mapped[str] = mapped_column(String(45), default="")
    details: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NotificationType(str, enum.Enum):
    stage_changed = "stage_changed"
    case_assigned = "case_assigned"
    approval_requested = "approval_requested"
    approval_result = "approval_result"
    completion_requested = "completion_requested"
    case_rejected = "case_rejected"
    general = "general"
    new_partner = "new_partner"


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notif_user_unread", "user_id", "is_read"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType, name="notification_type_enum"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    message: Mapped[str] = mapped_column(Text, default="")
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
