"""
Entity Rule — Product-level lending entity conditions.

Each row = one PRODUCT within an entity:
  e.g. "Rajhi_POS" (مصرف الراجحي — نقاط بيع), "Rajhi_Cash" (مصرف الراجحي — كاش)

Entities can have 1+ products. Priority is at the entity level (shared by all products).
Evaluation order:
  1. Filter by facility_type selected by partner
  2. Pre-filter using CR data + questions (before bank statement)
  3. Financial check using bank statement analysis
  4. Stop at first eligible product (sequential, priority-based)
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.compat import GUID, JSONType

from app.database import Base


class EntityRule(Base):
    """
    One row = one product of a lending entity.
    Products sharing entity_code belong to the same entity.
    Priority is at entity level (lower = higher priority).
    """

    __tablename__ = "entity_rules"
    __table_args__ = (
        Index("ix_entity_rules_active", "is_active"),
        Index("ix_entity_rules_priority", "priority"),
        Index("ix_entity_rules_product", "product_code", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )

    # ── Entity grouping ─────────────────────────────────
    entity_name: Mapped[str] = mapped_column(String(200), nullable=False)
    entity_code: Mapped[str] = mapped_column(String(50), nullable=False)  # NOT unique — shared by products

    # ── Product info ────────────────────────────────────
    product_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String(200), default="")

    # Which facility types this product serves: ["pos"], ["cash"], ["fleet"], or combo
    facility_types: Mapped[list] = mapped_column(JSONType(), nullable=False, default=list)

    priority: Mapped[int] = mapped_column(Integer, default=100)  # entity-level priority
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Pre-filter conditions (CR + questions, BEFORE bank statement) ──
    min_age_months: Mapped[int] = mapped_column(Integer, default=6)
    requires_pos: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_invoices: Mapped[bool] = mapped_column(Boolean, default=False)
    max_partners: Mapped[int | None] = mapped_column(Integer, nullable=True)  # null=any, 1=single
    accepts_foreign: Mapped[bool] = mapped_column(Boolean, default=True)
    blocked_activities: Mapped[list | None] = mapped_column(JSONType(), nullable=True)
    allowed_entity_types: Mapped[list | None] = mapped_column(JSONType(), nullable=True)

    # ── Financial conditions (from bank statement analysis) ──
    min_pos_rajhi: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_pos_other: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_total_deposits: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_total_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_profit_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.08 = 8%
    requires_stability_check: Mapped[bool] = mapped_column(Boolean, default=False)
    tax_returns_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tax_returns_frequency: Mapped[str | None] = mapped_column(String(20), nullable=True)  # quarterly/monthly
    financial_statement_rule: Mapped[str | None] = mapped_column(String(20), nullable=True)  # none/internal/certified/conditional

    # ── Output ──────────────────────────────────────────
    offer_code_prefix: Mapped[str] = mapped_column(String(10), default="")
    required_docs: Mapped[list | None] = mapped_column(JSONType(), nullable=True)
    extra_conditions: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
