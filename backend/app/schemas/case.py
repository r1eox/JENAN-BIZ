"""Pydantic schemas — Case, Stage, Notes, Assignments."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# ─── Stage History ──────────────────────────────────────

class StageHistoryResponse(BaseModel):
    id: UUID
    stage: str
    timestamp: datetime
    updated_by_name: str
    updated_by_role: str
    note: str = ""

    model_config = {"from_attributes": True}


# ─── Internal Note ──────────────────────────────────────

class NoteCreate(BaseModel):
    note: str = Field(..., min_length=1, max_length=2000)


class CompletionRequest(BaseModel):
    note: str = Field(default="", max_length=2000)
    required_docs: list[str] = Field(default_factory=list)


class NoteResponse(BaseModel):
    id: UUID
    author_name: str
    author_role: str
    note: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Approval ──────────────────────────────────────────

class ApprovalResponse(BaseModel):
    id: UUID
    stage: str
    requested_by_name: str
    requested_at: datetime
    approved_by_name: str = ""
    approved_at: datetime | None = None
    status: str
    note: str = ""

    model_config = {"from_attributes": True}


class ApprovalDecision(BaseModel):
    approved: bool
    note: str = ""


# ─── Assignment ────────────────────────────────────────

class AssignRequest(BaseModel):
    employee_id: UUID


class AssignmentResponse(BaseModel):
    id: UUID
    employee_name: str
    assigned_at: datetime

    model_config = {"from_attributes": True}


# ─── Stage Advance ─────────────────────────────────────

class AdvanceStageRequest(BaseModel):
    note: str = ""


class ProposeStageRequest(BaseModel):
    target_stage: str
    note: str = ""


# ─── Reject ────────────────────────────────────────────

class RejectRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=1000)


# ─── Override (Owner Only) ─────────────────────────────

class OverrideRequest(BaseModel):
    decision: str = Field(..., pattern="^(approve|reject|refer_review)$")
    reason: str = Field(..., min_length=5, max_length=2000)


class OverrideResponse(BaseModel):
    case_id: str
    decision: str
    reason: str
    overridden_by: str
    timestamp: str


# ─── Risk Flag ─────────────────────────────────────────

class RiskFlagSchema(BaseModel):
    code: str
    level: str
    title_ar: str
    detail_ar: str
    value: float | str = 0.0
    threshold: float | str = 0.0


# ─── Analysis Result (stored as JSON) ─────────────────

class AnalysisResultSchema(BaseModel):
    total_credits: float = 0
    total_debits: float = 0
    avg_monthly_credit: float = 0
    avg_monthly_debit: float = 0
    net_revenue: float = 0
    pos_total: float = 0
    pos_percentage: float = 0
    salary_transfers_total: float = 0
    returned_cheques_count: int = 0
    bounced_percentage: float = 0
    months_covered: int = 0
    date_range_start: str = ""
    date_range_end: str = ""
    total_transactions: int = 0
    duplicate_count: int = 0
    outlier_count: int = 0
    internal_transfer_count: int = 0
    reversal_count: int = 0
    categories: dict[str, float] = {}
    confidence_score: float = 0
    is_eligible: bool = False
    matched_entity: str | None = None
    offer_code: str | None = None
    issues: list[str] = []
    risk_flags: list[RiskFlagSchema] = []
    recommendation: str = ""  # auto_approve | manual_review | reject
    max_monthly_drop_pct: float = 0
    profit_ratio: float = 0


# ─── Case ──────────────────────────────────────────────

class CaseResponse(BaseModel):
    id: UUID
    display_id: str
    partner_id: UUID
    company_name: str = ""
    registration_number: str = ""
    entity_type: str = ""
    issue_date: str = ""
    age_in_months: int = 0
    stage: str
    is_eligible: bool = False
    analysis_progress: int = 0
    assigned_to: UUID | None = None
    partner_name: str = ""
    assigned_to_name: str = ""
    cr_file_name: str = ""
    bs_file_name: str = ""
    offer_code: str = ""
    result_summary: str = ""
    confidence_score: float = 0
    last_stage_change_at: datetime
    created_at: datetime
    updated_at: datetime

    # Override info (owner)
    is_overridden: bool = False
    override_decision: str = ""
    override_reason: str = ""
    overridden_at: datetime | None = None

    # Risk flags
    risk_flag_count: int = 0
    has_high_risk: bool = False
    validation_recommendation: str = ""

    # Populated only for owner role
    entity_name: str | None = None

    # Supplementary docs (uploaded by partner for completing_request)
    supplementary_docs: list[dict] = Field(default_factory=list)

    # Docs required by staff when requesting completion
    completion_required_docs: list[str] = Field(default_factory=list)

    # Analysis result (raw JSON)
    analysis_result: dict = Field(default_factory=dict)

    @field_validator('supplementary_docs', mode='before')
    @classmethod
    def coerce_supplementary_docs(cls, v):
        return v if isinstance(v, list) else []

    @field_validator('completion_required_docs', mode='before')
    @classmethod
    def coerce_completion_required_docs(cls, v):
        return v if isinstance(v, list) else []

    @field_validator('analysis_result', mode='before')
    @classmethod
    def coerce_analysis_result(cls, v):
        return v if isinstance(v, dict) else {}

    # Related
    stage_history: list[StageHistoryResponse] = []
    notes: list[NoteResponse] = []
    approvals: list[ApprovalResponse] = []

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    items: list[CaseResponse]
    total: int
    page: int
    size: int


# ─── KPIs ──────────────────────────────────────────────

class KPIResponse(BaseModel):
    total_cases: int = 0
    completed_cases: int = 0
    rejected_cases: int = 0
    pending_approval: int = 0
    overdue_cases: int = 0
    avg_transition_hours: float = 0
    stage_distribution: dict[str, int] = {}
    today_new: int = 0


class OwnerAnalyticsResponse(BaseModel):
    """Professional owner dashboard analytics."""
    total_requests: int = 0
    eligibility_rate: float = 0.0  # percentage
    entity_distribution: dict[str, int] = {}
    rejection_rate: float = 0.0
    avg_processing_hours: float = 0.0
    total_pos_volume: float = 0.0
    expected_total_financing: float = 0.0
    completed_this_month: int = 0
    rejected_this_month: int = 0
    new_this_month: int = 0
    overridden_count: int = 0
    high_risk_count: int = 0
    auto_approved_count: int = 0
    manual_review_count: int = 0
