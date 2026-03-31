"""
Entity Rules API — CRUD for lending entity rules (owner only).
Includes Smart Routing priority reorder endpoint.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.entity_rule import EntityRule
from app.models.audit import AuditLog, AuditAction
from app.core.rbac import require_role, require_permission

router = APIRouter(prefix="/entity-rules", tags=["entity-rules"])


class EntityRuleCreate(BaseModel):
    entity_name: str = Field(..., min_length=2)
    entity_code: str = Field(..., min_length=2, max_length=50)
    product_code: str = Field(..., min_length=2, max_length=50)
    product_name: str = ""
    facility_types: list[str] = ["pos"]
    priority: int = 100
    min_age_months: int = 6
    requires_pos: bool = False
    requires_invoices: bool = False
    max_partners: int | None = None
    accepts_foreign: bool = True
    blocked_activities: list[str] | None = None
    allowed_entity_types: list[str] | None = None
    min_pos_rajhi: float | None = None
    min_pos_other: float | None = None
    min_total_deposits: float | None = None
    min_total_revenue: float | None = None
    min_profit_ratio: float | None = None
    requires_stability_check: bool = False
    tax_returns_count: int | None = None
    tax_returns_frequency: str | None = None
    financial_statement_rule: str | None = None
    offer_code_prefix: str = ""
    extra_conditions: dict | None = None
    required_docs: list[str] | None = None
    description: str = ""


class EntityRuleUpdate(BaseModel):
    entity_name: str | None = None
    product_name: str | None = None
    facility_types: list[str] | None = None
    priority: int | None = None
    is_active: bool | None = None
    min_age_months: int | None = None
    requires_pos: bool | None = None
    requires_invoices: bool | None = None
    max_partners: int | None = None
    accepts_foreign: bool | None = None
    blocked_activities: list[str] | None = None
    allowed_entity_types: list[str] | None = None
    min_pos_rajhi: float | None = None
    min_pos_other: float | None = None
    min_total_deposits: float | None = None
    min_total_revenue: float | None = None
    min_profit_ratio: float | None = None
    requires_stability_check: bool | None = None
    tax_returns_count: int | None = None
    tax_returns_frequency: str | None = None
    financial_statement_rule: str | None = None
    offer_code_prefix: str | None = None
    extra_conditions: dict | None = None
    required_docs: list[str] | None = None
    description: str | None = None


class EntityRuleResponse(BaseModel):
    id: uuid.UUID
    entity_name: str
    entity_code: str
    product_code: str
    product_name: str
    facility_types: list[str]
    priority: int
    is_active: bool
    min_age_months: int
    requires_pos: bool
    requires_invoices: bool
    max_partners: int | None
    accepts_foreign: bool
    blocked_activities: list[str] | None
    allowed_entity_types: list[str] | None
    min_pos_rajhi: float | None
    min_pos_other: float | None
    min_total_deposits: float | None
    min_total_revenue: float | None
    min_profit_ratio: float | None
    requires_stability_check: bool
    tax_returns_count: int | None
    tax_returns_frequency: str | None
    financial_statement_rule: str | None
    offer_code_prefix: str
    extra_conditions: dict | None
    required_docs: list[str] | None
    description: str

    model_config = {"from_attributes": True}


class ReorderItem(BaseModel):
    """Single item in reorder request."""
    id: uuid.UUID
    priority: int = Field(..., ge=1)


class ReorderRequest(BaseModel):
    """Reorder entity priority list."""
    items: list[ReorderItem] = Field(..., min_length=1)


@router.get("/", response_model=list[EntityRuleResponse])
async def list_rules(
    current_user: User = Depends(require_permission("view_partner_files")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EntityRule).order_by(EntityRule.priority.asc())
    )
    return [EntityRuleResponse.model_validate(r) for r in result.scalars().all()]


@router.post("/", response_model=EntityRuleResponse, status_code=201)
async def create_rule(
    body: EntityRuleCreate,
    current_user: User = Depends(require_permission("add_entities")),
    db: AsyncSession = Depends(get_db),
):
    # Check duplicate product code
    existing = await db.execute(
        select(EntityRule).where(EntityRule.product_code == body.product_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, "كود المنتج مسجّل مسبقاً")

    rule = EntityRule(**body.model_dump())
    db.add(rule)
    await db.flush()

    audit = AuditLog(
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role.value,
        action=AuditAction.entity_rule_created,
        details={"rule_id": str(rule.id), "entity_code": rule.entity_code},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(rule)
    return EntityRuleResponse.model_validate(rule)


@router.patch("/{rule_id}", response_model=EntityRuleResponse)
async def update_rule(
    rule_id: uuid.UUID,
    body: EntityRuleUpdate,
    current_user: User = Depends(require_permission("edit_entities")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EntityRule).where(EntityRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "القاعدة غير موجودة")

    update_data = body.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    audit = AuditLog(
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role.value,
        action=AuditAction.entity_rule_updated,
        details={"rule_id": str(rule_id), "changes": update_data},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(rule)
    return EntityRuleResponse.model_validate(rule)


@router.delete("/{rule_id}")
async def deactivate_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(require_permission("edit_entities")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EntityRule).where(EntityRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "القاعدة غير موجودة")

    rule.is_active = False
    await db.commit()
    return {"status": "deactivated"}


# ─── Reorder entity priorities (Smart Routing) ───────

@router.post("/reorder", response_model=list[EntityRuleResponse])
async def reorder_rules(
    body: ReorderRequest,
    current_user: User = Depends(require_permission("edit_entities")),
    db: AsyncSession = Depends(get_db),
):
    """
    Reorder entity evaluation priorities for the Smart Routing Engine.

    Rules:
    - Each entity gets a unique priority (lower = evaluated first)
    - Duplicate priorities are rejected
    - Change is atomic — all or nothing
    - Does NOT affect in-progress cases (they keep their matched entity)
    - Audit-logged for accountability
    """
    # Validate unique priorities
    priorities = [item.priority for item in body.items]
    if len(priorities) != len(set(priorities)):
        raise HTTPException(
            422, "لا يمكن تكرار نفس الأولوية — كل جهة يجب أن تحصل على أولوية فريدة"
        )

    # Validate all rule IDs exist
    rule_ids = [item.id for item in body.items]
    result = await db.execute(
        select(EntityRule).where(EntityRule.id.in_(rule_ids))
    )
    rules_map = {r.id: r for r in result.scalars().all()}

    if len(rules_map) != len(rule_ids):
        missing = set(rule_ids) - set(rules_map.keys())
        raise HTTPException(
            404,
            f"جهات غير موجودة: {', '.join(str(m) for m in missing)}"
        )

    # Build old→new mapping for audit
    old_order = {
        r_id: {"name": r.entity_name, "old_priority": r.priority}
        for r_id, r in rules_map.items()
    }

    # Apply new priorities
    for item in body.items:
        rules_map[item.id].priority = item.priority

    # Audit log
    changes = []
    for item in body.items:
        info = old_order[item.id]
        if info["old_priority"] != item.priority:
            changes.append({
                "entity": info["name"],
                "old_priority": info["old_priority"],
                "new_priority": item.priority,
            })

    if changes:
        audit = AuditLog(
            user_id=current_user.id,
            user_name=current_user.name,
            user_role=current_user.role.value,
            action=AuditAction.entity_rules_reordered,
            details={"changes": changes, "total_entities": len(body.items)},
        )
        db.add(audit)

    await db.commit()

    # Return updated list sorted by priority
    result = await db.execute(
        select(EntityRule).order_by(EntityRule.priority.asc())
    )
    return [EntityRuleResponse.model_validate(r) for r in result.scalars().all()]


# ─── Toggle entity active/inactive ───────────────────

@router.patch("/{rule_id}/toggle")
async def toggle_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(require_permission("edit_entities")),
    db: AsyncSession = Depends(get_db),
):
    """Toggle entity active/inactive status."""
    result = await db.execute(select(EntityRule).where(EntityRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "القاعدة غير موجودة")

    rule.is_active = not rule.is_active
    new_status = "مفعّلة" if rule.is_active else "معطّلة"

    audit = AuditLog(
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role.value,
        action=AuditAction.entity_rule_updated,
        details={
            "rule_id": str(rule_id),
            "entity_name": rule.entity_name,
            "action": "toggle",
            "new_status": new_status,
        },
    )
    db.add(audit)

    await db.commit()
    return {"status": new_status, "is_active": rule.is_active}
