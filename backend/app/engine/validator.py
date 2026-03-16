"""
Validation Engine — v2 (Production-Ready)
──────────────────────────────────────────
Post-analysis validation with confidence scoring and
Conditional Auto-Approval logic.

v2 enhancements:
  ✓ Risk-flag-aware approval decisions
  ✓ Conditional auto-approval (single entity + safety margin + complete docs + no risk flags)
  ✓ Improved confidence scoring
  ✓ Monthly variance and data-gap detection
"""

from __future__ import annotations

from dataclasses import dataclass
from loguru import logger

from app.engine.analyzer import AnalysisResult, RiskLevel

# ─── Constants ─────────────────────────────────────────

MIN_CONFIDENCE_FOR_AUTO = 0.85
MIN_CONFIDENCE_FOR_REVIEW = 0.70
MAX_DUPLICATE_RATIO = 0.10
MAX_OUTLIER_RATIO = 0.05
MAX_MONTHLY_VARIANCE = 3.0
SAFETY_MARGIN = 0.10  # 10% above minimum thresholds


@dataclass
class ValidationResult:
    is_valid: bool = True
    confidence: float = 0.0
    recommendation: str = "manual_review"  # auto_approve | manual_review | reject
    issues: list[str] | None = None
    risk_flag_count: int = 0
    has_high_risk: bool = False
    auto_approval_eligible: bool = False
    auto_approval_reasons: list[str] | None = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.auto_approval_reasons is None:
            self.auto_approval_reasons = []


def validate_analysis(
    analysis: AnalysisResult,
    *,
    eligible_entity_count: int = 0,
    docs_complete: bool = False,
) -> ValidationResult:
    """
    Validate analysis results and determine recommendation.

    Parameters:
        analysis: The financial analysis result.
        eligible_entity_count: Number of entities that passed pre-filter/financial check.
        docs_complete: Whether all required documents have been uploaded.

    Returns:
        ValidationResult with recommendation (auto_approve / manual_review / reject).
    """
    result = ValidationResult()
    confidence = analysis.confidence_score
    issues = list(analysis.issues)

    # ── 1. Confidence scoring adjustments ────────────

    # Duplicate ratio penalty
    if analysis.total_transactions > 0:
        dup_ratio = analysis.duplicate_count / analysis.total_transactions
        if dup_ratio > MAX_DUPLICATE_RATIO:
            penalty = min((dup_ratio - MAX_DUPLICATE_RATIO) * 2, 0.15)
            confidence -= penalty
            issues.append(
                f"نسبة مكررات عالية: {dup_ratio:.0%} (الحد {MAX_DUPLICATE_RATIO:.0%})"
            )

    # Outlier ratio penalty
    if analysis.total_transactions > 0:
        outlier_ratio = analysis.outlier_count / analysis.total_transactions
        if outlier_ratio > MAX_OUTLIER_RATIO:
            penalty = min((outlier_ratio - MAX_OUTLIER_RATIO) * 1.5, 0.10)
            confidence -= penalty
            issues.append(f"نسبة قيم شاذة عالية: {outlier_ratio:.0%}")

    # Monthly variance penalty
    if len(analysis.monthly) >= 2:
        credits = [m.total_credit for m in analysis.monthly if m.total_credit > 0]
        if credits:
            avg_c = sum(credits) / len(credits)
            if avg_c > 0:
                max_c = max(credits)
                min_c = min(credits)
                variance_ratio = (max_c - min_c) / avg_c
                if variance_ratio > MAX_MONTHLY_VARIANCE:
                    penalty = min((variance_ratio - MAX_MONTHLY_VARIANCE) * 0.05, 0.15)
                    confidence -= penalty
                    issues.append(
                        f"تباين شهري كبير: {variance_ratio:.1f}x (الحد {MAX_MONTHLY_VARIANCE}x)"
                    )

    # Short data period
    if analysis.months_covered < 3:
        confidence -= 0.10
        issues.append(f"فترة بيانات قصيرة: {analysis.months_covered} أشهر (المطلوب 3+)")

    # Internal transfers
    if analysis.internal_transfer_count > 0:
        issues.append(
            f"تحويلات داخلية مستبعدة: {analysis.internal_transfer_count} معاملة"
        )

    # Reversals
    if analysis.reversal_count > 0:
        issues.append(f"عمليات عكسية مستبعدة: {analysis.reversal_count} معاملة")

    # Zero revenue
    if analysis.total_credits == 0:
        confidence = 0.0
        issues.append("لا توجد إيرادات — بيانات غير صالحة")

    confidence = max(0.0, min(1.0, confidence))
    result.confidence = round(confidence, 3)
    result.issues = issues

    # ── 2. Risk flags evaluation ──────────────────────

    risk_flags = analysis.risk_flags
    result.risk_flag_count = len(risk_flags)
    result.has_high_risk = any(f.level == RiskLevel.HIGH for f in risk_flags)

    # ── 3. Conditional auto-approval checks ──────────

    auto_reasons: list[str] = []
    auto_eligible = True

    # Condition A: Exactly one eligible entity
    if eligible_entity_count != 1:
        auto_eligible = False
        if eligible_entity_count == 0:
            auto_reasons.append("لا توجد جهات مؤهلة")
        else:
            auto_reasons.append(
                f"تعدد الجهات المؤهلة ({eligible_entity_count}) — يستلزم اختيار يدوي"
            )

    # Condition B: Confidence above threshold
    if confidence < MIN_CONFIDENCE_FOR_AUTO:
        auto_eligible = False
        auto_reasons.append(
            f"مستوى الثقة ({confidence:.0%}) أقل من الحد ({MIN_CONFIDENCE_FOR_AUTO:.0%})"
        )

    # Condition C: All documents complete
    if not docs_complete:
        auto_eligible = False
        auto_reasons.append("المستندات غير مكتملة")

    # Condition D: No risk flags
    if result.risk_flag_count > 0:
        auto_eligible = False
        flag_codes = ", ".join(f.code for f in risk_flags)
        auto_reasons.append(f"يوجد أعلام مخاطر ({flag_codes})")

    # Condition E: Numbers exceed minimums with safety margin
    # (Per-entity checks aren't available here — handled in rule_engine)
    # This is a general revenue sanity check
    if analysis.avg_monthly_credit < 50_000:
        auto_eligible = False
        auto_reasons.append(
            f"متوسط الإيرادات الشهرية ({analysis.avg_monthly_credit:,.0f}) "
            f"أقل من الحد الأدنى العام"
        )

    result.auto_approval_eligible = auto_eligible
    result.auto_approval_reasons = auto_reasons

    # ── 4. Final recommendation ──────────────────────

    if analysis.total_credits == 0 or confidence < 0.30:
        result.is_valid = False
        result.recommendation = "reject"
    elif auto_eligible:
        result.recommendation = "auto_approve"
    elif confidence >= MIN_CONFIDENCE_FOR_REVIEW:
        result.recommendation = "manual_review"
    else:
        result.is_valid = False
        result.recommendation = "reject"

    logger.info(
        f"Validation: confidence={result.confidence:.2f}, "
        f"recommendation={result.recommendation}, "
        f"auto_eligible={auto_eligible}, risk_flags={result.risk_flag_count}"
    )

    return result
