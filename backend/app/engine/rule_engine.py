"""
Rule Engine — Smart Routing Engine v2
──────────────────────────────────────
Two-phase entity evaluation:

Phase 1 — Pre-filter (CR + Questions, BEFORE bank statement):
  • Filter products by facility type
  • Check age, POS requirement, partner count, nationality, activity, entity type
  • Returns list of eligible products
  • If NONE → reject immediately, no bank statement requested

Phase 2 — Financial check (AFTER bank statement):
  • Evaluate products sequentially by entity priority
  • Check POS amounts, deposits, revenue, profit ratio, stability
  • STOP at first eligible product
  • If not eligible → try next product in priority order
  • Partner NEVER sees which entity rejected them

Priority order is DB-driven, controlled by Owner.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.entity_rule import EntityRule
from app.models.case import Case
from app.engine.analyzer import AnalysisResult


# ─── Pre-filter Result ─────────────────────────────────

@dataclass
class PreFilterResult:
    """Result from Phase 1 pre-filtering."""
    has_eligible: bool = False
    eligible_products: list[dict] = field(default_factory=list)
    required_bs_months: int = 0
    rejection_log: list[str] = field(default_factory=list)  # internal-only


def calculate_required_bs_months(age_months: int) -> int:
    """
    Bank statement duration based on business age.
    < 6  → 0  (reject)
    6–11 → full age
    ≥ 12 → 12 months max
    """
    if age_months < 6:
        return 0
    if age_months <= 11:
        return age_months
    return 12


async def pre_filter_entities(
    db: AsyncSession,
    facility_type: str,
    age_months: int,
    entity_type: str,
    activity: str,
    has_pos: bool,
    has_invoices: bool,
    partner_count: int,
    is_saudi: bool,
) -> PreFilterResult:
    """
    Phase 1 — Pre-filter: evaluate products using CR data + questions only.
    No bank statement needed yet.

    Returns eligible products sorted by entity priority.
    If none eligible → reject immediately without requesting bank statement.
    """
    result = PreFilterResult()

    # Age < 6 → absolute reject
    if age_months < 6:
        result.rejection_log.append(f"عمر المنشأة ({age_months} شهر) أقل من 6 أشهر — رفض مباشر")
        return result

    result.required_bs_months = calculate_required_bs_months(age_months)

    # Load active products for selected facility type
    all_rules = await db.execute(
        select(EntityRule)
        .where(EntityRule.is_active == True)  # noqa: E712
        .order_by(EntityRule.priority.asc())
    )
    rules = all_rules.scalars().all()

    if not rules:
        result.rejection_log.append("لا توجد جهات تمويل فعّالة في النظام")
        return result

    for rule in rules:
        # Skip if product doesn't serve selected facility type
        if facility_type not in (rule.facility_types or []):
            continue

        reasons = _pre_filter_check(rule, age_months, entity_type, activity, has_pos, has_invoices, partner_count, is_saudi)

        if not reasons:
            result.eligible_products.append({
                "product_code": rule.product_code,
                "entity_name": rule.entity_name,
                "entity_code": rule.entity_code,
                "product_name": rule.product_name,
                "priority": rule.priority,
            })
            result.rejection_log.append(
                f"[✅ مبدئياً] {rule.entity_name} / {rule.product_name} (أولوية {rule.priority})"
            )
            logger.info(
                f"[SmartRouter:PreFilter] ✅ {rule.product_code} passed "
                f"(entity={rule.entity_name}, priority={rule.priority})"
            )
        else:
            result.rejection_log.append(
                f"[❌ استبعاد] {rule.entity_name} / {rule.product_name}: " + " | ".join(reasons)
            )
            logger.info(
                f"[SmartRouter:PreFilter] ❌ {rule.product_code} excluded: "
                f"{len(reasons)} reason(s)"
            )

    result.has_eligible = len(result.eligible_products) > 0
    return result


def _pre_filter_check(
    rule: EntityRule,
    age_months: int,
    entity_type: str,
    activity: str,
    has_pos: bool,
    has_invoices: bool,
    partner_count: int,
    is_saudi: bool,
) -> list[str]:
    """Check pre-filter conditions (CR + questions). Returns [] if passes."""
    reasons: list[str] = []

    # Age
    if age_months < rule.min_age_months:
        reasons.append(f"عمر المنشأة ({age_months}) < الحد الأدنى ({rule.min_age_months})")

    # POS requirement
    if rule.requires_pos and not has_pos:
        reasons.append("المنتج يتطلب نقاط بيع والمنشأة لا تملك")

    # Invoices requirement (SDF_INVOICES path)
    if rule.requires_invoices and not has_invoices:
        reasons.append("المنتج يتطلب فواتير مبيعات منتظمة والمنشأة لا تملك")

    # Partner count
    if rule.max_partners is not None and partner_count > rule.max_partners:
        reasons.append(f"عدد الشركاء ({partner_count}) > الحد ({rule.max_partners})")

    # Nationality
    if not rule.accepts_foreign and not is_saudi:
        reasons.append("المنتج لا يقبل مستثمرين أجانب")

    # Blocked activities
    if rule.blocked_activities and activity:
        for blocked in rule.blocked_activities:
            if blocked in activity:
                reasons.append(f"النشاط '{activity}' محظور لهذا المنتج")
                break

    # Allowed entity types — flexible substring match (both directions)
    if rule.allowed_entity_types and entity_type:
        entity_lower = entity_type.lower()
        matched = any(
            allowed.lower() in entity_lower or entity_lower in allowed.lower()
            for allowed in rule.allowed_entity_types
        )
        if not matched:
            reasons.append(f"نوع الكيان ({entity_type}) غير مقبول لهذا المنتج")

    return reasons


# ─── Phase 2 — Financial Check ─────────────────────────

@dataclass
class FinancialCheckResult:
    """Result from Phase 2 financial evaluation."""
    matched: bool = False
    matched_rule: EntityRule | None = None
    required_docs: list[str] = field(default_factory=list)
    evaluation_log: list[str] = field(default_factory=list)  # internal-only


async def financial_check(
    db: AsyncSession,
    analysis: AnalysisResult,
    eligible_product_codes: list[str],
    is_rajhi_bank: bool = False,
) -> FinancialCheckResult:
    """
    Phase 2 — Financial check: evaluate eligible products sequentially.
    Uses bank statement analysis data.
    STOPS at first eligible product.
    """
    result = FinancialCheckResult()

    if not eligible_product_codes:
        result.evaluation_log.append("لا توجد منتجات مؤهلة للتقييم المالي")
        return result

    # Load the eligible products in priority order
    rules_result = await db.execute(
        select(EntityRule)
        .where(EntityRule.product_code.in_(eligible_product_codes))
        .where(EntityRule.is_active == True)  # noqa: E712
        .order_by(EntityRule.priority.asc())
    )
    rules = rules_result.scalars().all()

    for idx, rule in enumerate(rules, start=1):
        logger.info(
            f"[SmartRouter:Financial] Evaluating {idx}/{len(rules)}: "
            f"{rule.product_code} ({rule.entity_name}, priority={rule.priority})"
        )

        reasons = _financial_check_rule(rule, analysis, is_rajhi_bank)

        if not reasons:
            # ✅ MATCH — stop immediately
            result.matched = True
            result.matched_rule = rule
            result.required_docs = rule.required_docs or []
            result.evaluation_log.append(
                f"[✅ مؤهل مالياً] {rule.entity_name} / {rule.product_name} "
                f"(أولوية {rule.priority})"
            )
            logger.info(
                f"[SmartRouter:Financial] ✅ Matched: {rule.product_code}"
            )
            return result
        else:
            result.evaluation_log.append(
                f"[❌ غير مؤهل مالياً] {rule.entity_name} / {rule.product_name}: "
                + " | ".join(reasons)
            )
            logger.info(
                f"[SmartRouter:Financial] ❌ {rule.product_code}: "
                f"{len(reasons)} reason(s)"
            )

    logger.info(
        f"[SmartRouter:Financial] No product matched after evaluating "
        f"{len(rules)} products"
    )
    return result


def _financial_check_rule(
    rule: EntityRule,
    analysis: AnalysisResult,
    is_rajhi_bank: bool,
) -> list[str]:
    """Check financial conditions for a single product. Returns [] if passes."""
    reasons: list[str] = []

    # POS check (Rajhi/Emkan: threshold depends on bank)
    if rule.min_pos_rajhi is not None or rule.min_pos_other is not None:
        threshold = rule.min_pos_rajhi if is_rajhi_bank else rule.min_pos_other
        if threshold is not None and analysis.pos_total < threshold:
            bank_label = "الراجحي" if is_rajhi_bank else "خارج الراجحي"
            reasons.append(
                f"إجمالي نقاط البيع ({analysis.pos_total:,.0f}) "
                f"< المطلوب ({threshold:,.0f}) [حساب {bank_label}]"
            )

    # Total deposits check (Rajhi_Cash)
    if rule.min_total_deposits is not None:
        if analysis.total_credits < rule.min_total_deposits:
            reasons.append(
                f"إجمالي الإيداعات ({analysis.total_credits:,.0f}) "
                f"< المطلوب ({rule.min_total_deposits:,.0f})"
            )

    # Total revenue check (SDF, Amlak, Sahl)
    if rule.min_total_revenue is not None:
        if analysis.total_credits < rule.min_total_revenue:
            reasons.append(
                f"إجمالي الإيرادات ({analysis.total_credits:,.0f}) "
                f"< المطلوب ({rule.min_total_revenue:,.0f})"
            )

    # Profit ratio check (Amlak, Sahl)
    if rule.min_profit_ratio is not None and analysis.total_credits > 0:
        actual_ratio = analysis.net_revenue / analysis.total_credits
        if actual_ratio < rule.min_profit_ratio:
            reasons.append(
                f"نسبة الربح ({actual_ratio:.1%}) "
                f"< المطلوب ({rule.min_profit_ratio:.0%})"
            )

    # Revenue stability check (SDF)
    if rule.requires_stability_check and analysis.monthly:
        for i in range(1, len(analysis.monthly)):
            prev = analysis.monthly[i - 1].total_credit
            curr = analysis.monthly[i].total_credit
            if prev > 0:
                drop = (prev - curr) / prev
                if drop > 0.20:
                    reasons.append(
                        f"انخفاض في الإيرادات بين الشهور يتجاوز 20% "
                        f"({drop:.0%} في شهر {analysis.monthly[i].month}/{analysis.monthly[i].year})"
                    )
                    break

    return reasons


# ─── Legacy wrapper for backward compatibility ─────────

async def match_entity(
    db: AsyncSession,
    analysis: AnalysisResult,
    cr_age_months: int,
    entity_type: str = "",
    eligible_product_codes: list[str] | None = None,
    is_rajhi_bank: bool = False,
) -> tuple[EntityRule | None, list[str]]:
    """
    Backward-compatible wrapper.
    If eligible_product_codes provided, runs Phase 2 only.
    Otherwise runs against all active rules (fallback).
    """
    if eligible_product_codes:
        result = await financial_check(db, analysis, eligible_product_codes, is_rajhi_bank)
        return result.matched_rule, result.evaluation_log
    else:
        # Fallback: load all active rules and try financial check
        all_result = await db.execute(
            select(EntityRule)
            .where(EntityRule.is_active == True)  # noqa: E712
            .order_by(EntityRule.priority.asc())
        )
        all_codes = [r.product_code for r in all_result.scalars().all()]
        result = await financial_check(db, analysis, all_codes, is_rajhi_bank)
        return result.matched_rule, result.evaluation_log


async def generate_offer_code(db: AsyncSession, prefix: str) -> str:
    """Generate a sequential offer code like 'RAJ-0042'."""
    result = await db.execute(
        select(func.count())
        .select_from(Case)
        .where(Case.offer_code.like(f"{prefix}-%"))
    )
    count = result.scalar() or 0
    return f"{prefix}-{count + 1:04d}"
