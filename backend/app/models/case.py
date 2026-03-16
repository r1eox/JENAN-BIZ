"""
Jenan BIZ — Case & Stage Models

Stages:
  1. analyzing  2. completing_request  3. fee_contract_signed  4. completing_forms
  5. submitted  6. approved  7. signed  8. facilities_transferred  9. fees_received
  + rejected (terminal)

Related tables:
  - cases               Main case record
  - case_stage_history   Every stage transition + audit
  - case_assignments     Employee assignment log
  - internal_notes       Internal staff notes
  - stage_approvals      Gated stage approval requests
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    String, Text, Boolean, Integer, Float, DateTime,
    ForeignKey, Enum as SAEnum, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.compat import GUID, JSONType

from app.database import Base


# ─── Stage Enum ─────────────────────────────────────────

class CaseStage(str, enum.Enum):
    analyzing = "analyzing"
    completing_request = "completing_request"
    fee_contract_signed = "fee_contract_signed"
    completing_forms = "completing_forms"
    submitted = "submitted"
    approved = "approved"
    signed = "signed"
    facilities_transferred = "facilities_transferred"
    fees_received = "fees_received"
    rejected = "rejected"


STAGES_ORDER = [
    CaseStage.analyzing,
    CaseStage.completing_request,
    CaseStage.fee_contract_signed,
    CaseStage.completing_forms,
    CaseStage.submitted,
    CaseStage.approved,
    CaseStage.signed,
    CaseStage.facilities_transferred,
    CaseStage.fees_received,
]

# Gated stages — require supervisor/owner approval
GATED_STAGES = {
    CaseStage.submitted,
    CaseStage.approved,
    CaseStage.signed,
    CaseStage.facilities_transferred,
    CaseStage.fees_received,
    CaseStage.rejected,
}


class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


# ─── Case ───────────────────────────────────────────────

class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (
        Index("ix_cases_stage", "stage"),
        Index("ix_cases_partner", "partner_id"),
        Index("ix_cases_assigned", "assigned_to"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    display_id: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)

    # Partner
    partner_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )

    # Company info (from CR analysis)
    company_name: Mapped[str] = mapped_column(String(300), default="")
    registration_number: Mapped[str] = mapped_column(String(50), default="")
    entity_type: Mapped[str] = mapped_column(String(100), default="")
    issue_date: Mapped[str] = mapped_column(String(20), default="")
    age_in_months: Mapped[int] = mapped_column(Integer, default=0)
    activity: Mapped[str] = mapped_column(String(300), default="")

    # Facility type selected by partner (pos / cash / fleet)
    facility_type: Mapped[str] = mapped_column(String(20), default="")

    # Partner questions (answered after CR, before bank statement)
    has_pos: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_invoices: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    partner_count: Mapped[int] = mapped_column(Integer, default=1)  # 1 or 2+
    is_saudi: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Smart routing tracking
    current_product_code: Mapped[str] = mapped_column(String(50), default="")
    pre_filter_passed: Mapped[list | None] = mapped_column(JSONType(), nullable=True)
    required_bs_months: Mapped[int] = mapped_column(Integer, default=0)

    # Stage workflow
    stage: Mapped[CaseStage] = mapped_column(
        SAEnum(CaseStage, name="case_stage_enum"),
        nullable=False,
        default=CaseStage.analyzing,
    )
    is_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    analysis_progress: Mapped[int] = mapped_column(Integer, default=0)  # 0–100

    # Assignment
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True
    )

    # Files
    cr_file_path: Mapped[str] = mapped_column(String(500), default="")
    cr_file_name: Mapped[str] = mapped_column(String(300), default="")
    bs_file_path: Mapped[str] = mapped_column(String(500), default="")
    bs_file_name: Mapped[str] = mapped_column(String(300), default="")

    # Analysis results (JSON blob)
    analysis_result: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Entity matching (internal — only owner sees entity_name)
    offer_code: Mapped[str] = mapped_column(String(30), default="")
    entity_name: Mapped[str] = mapped_column(String(200), default="")  # HIDDEN except owner

    # Owner Override (Manual Decision)
    is_overridden: Mapped[bool] = mapped_column(Boolean, default=False)
    override_decision: Mapped[str] = mapped_column(String(30), default="")  # approve | reject | refer_review
    override_reason: Mapped[str] = mapped_column(Text, default="")
    overridden_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True
    )
    overridden_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Risk Flags (populated by validator)
    risk_flags: Mapped[list | None] = mapped_column(JSONType(), nullable=True)
    risk_flag_count: Mapped[int] = mapped_column(Integer, default=0)
    has_high_risk: Mapped[bool] = mapped_column(Boolean, default=False)

    # Validation recommendation
    validation_recommendation: Mapped[str] = mapped_column(String(30), default="")  # auto_approve | manual_review | reject

    # Supplementary documents (uploaded when completing_request)
    supplementary_docs: Mapped[list | None] = mapped_column(JSONType(), nullable=True)

    # Result
    result_summary: Mapped[str] = mapped_column(Text, default="")

    # SLA tracking
    last_stage_change_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    stage_history = relationship("CaseStageHistory", back_populates="case", lazy="selectin", order_by="CaseStageHistory.timestamp")
    notes = relationship("InternalNote", back_populates="case", lazy="selectin", order_by="InternalNote.created_at")
    approvals = relationship("StageApproval", back_populates="case", lazy="selectin")
    assignments = relationship("CaseAssignment", back_populates="case", lazy="selectin")


# ─── Stage History (Audit Log) ──────────────────────────

class CaseStageHistory(Base):
    __tablename__ = "case_stage_history"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    stage: Mapped[CaseStage] = mapped_column(
        SAEnum(CaseStage, name="case_stage_enum", create_type=False), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_by: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    updated_by_role: Mapped[str] = mapped_column(String(20), nullable=False)
    updated_by_name: Mapped[str] = mapped_column(String(200), default="")
    note: Mapped[str] = mapped_column(Text, default="")
    attachments: Mapped[list | None] = mapped_column(JSONType(), nullable=True)

    case = relationship("Case", back_populates="stage_history")


# ─── Internal Notes ─────────────────────────────────────

class InternalNote(Base):
    __tablename__ = "internal_notes"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    author_name: Mapped[str] = mapped_column(String(200), default="")
    author_role: Mapped[str] = mapped_column(String(20), default="")
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="notes")


# ─── Stage Approvals ───────────────────────────────────

class StageApproval(Base):
    __tablename__ = "stage_approvals"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    stage: Mapped[CaseStage] = mapped_column(
        SAEnum(CaseStage, name="case_stage_enum", create_type=False), nullable=False
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    requested_by_name: Mapped[str] = mapped_column(String(200), default="")
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True
    )
    approved_by_name: Mapped[str] = mapped_column(String(200), default="")
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[ApprovalStatus] = mapped_column(
        SAEnum(ApprovalStatus, name="approval_status_enum"),
        default=ApprovalStatus.pending,
    )
    note: Mapped[str] = mapped_column(Text, default="")

    case = relationship("Case", back_populates="approvals")


# ─── Case Assignment Log ───────────────────────────────

class CaseAssignment(Base):
    __tablename__ = "case_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    employee_name: Mapped[str] = mapped_column(String(200), default="")
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assigned_by: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )

    case = relationship("Case", back_populates="assignments")
