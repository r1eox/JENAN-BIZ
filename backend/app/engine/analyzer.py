"""
Financial Analyzer — v2 (Production-Ready)
──────────────────────────────────────────
Rule-based analysis of parsed bank statement transactions.

v2 enhancements:
  ✓ Skips duplicates, internal transfers, and paired reversals
  ✓ Generates Risk Flags for borderline numbers
  ✓ Revenue fluctuation tracking per-month
  ✓ Profit margin analysis
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from collections import defaultdict

from loguru import logger

from app.engine import Transaction, ParseResult


# ─── Transaction Categories ────────────────────────────

CATEGORY_RULES: dict[str, list[str]] = {
    "pos": [
        "pos", "نقطة بيع", "نقاط البيع", "point of sale", "مبيعات",
        "mada", "مدى", "visa", "فيزا", "mastercard", "ماستر",
    ],
    "salary_transfer": [
        "راتب", "رواتب", "salary", "payroll", "أجور", "wages",
        "مكافأة دورية", "تحويل راتب",
    ],
    "government": [
        "حكوم", "government", "sadad", "سداد", "gosi", "التأمينات",
        "الزكاة", "vat", "ضريبة", "zakat", "التأمين الاجتماعي",
        "وزارة", "هيئة", "مصلحة",
    ],
    "loan_payment": [
        "قسط", "أقساط", "installment", "تمويل", "financing",
        "loan", "قرض", "سداد قرض",
    ],
    "rent": [
        "إيجار", "ايجار", "rent", "أجرة", "عقار",
    ],
    "transfer_in": [
        "تحويل وارد", "حوالة واردة", "incoming transfer", "إيداع تحويل",
    ],
    "transfer_out": [
        "تحويل صادر", "حوالة صادرة", "outgoing transfer", "تحويل محلي",
        "حوالة دولية", "swift", "سويفت",
    ],
    "cash_deposit": [
        "إيداع نقدي", "cash deposit", "إيداع", "deposit",
    ],
    "cash_withdrawal": [
        "سحب نقدي", "atm", "صراف", "سحب", "withdrawal",
    ],
    "returned_cheque": [
        "شيك مرتجع", "شيك راجع", "returned cheque", "bounced",
        "شيكات مرتجعة", "رفض شيك",
    ],
    "cheque": [
        "شيك", "cheque", "check",
    ],
    "bank_fee": [
        "عمولة", "رسوم", "رسم", "commission", "fee", "charge",
        "خدمات بنكية", "bank charges",
    ],
    "other": [],
}


# ─── Risk Flag Definitions ─────────────────────────────

class RiskLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RiskFlag:
    code: str
    level: str  # RiskLevel
    title_ar: str
    detail_ar: str
    value: float | str = 0.0
    threshold: float | str = 0.0


@dataclass
class MonthlyBreakdown:
    year: int
    month: int
    total_credit: float = 0.0
    total_debit: float = 0.0
    pos_credit: float = 0.0
    salary_transfers: float = 0.0
    loan_payments: float = 0.0
    government_payments: float = 0.0
    returned_cheques: int = 0
    transaction_count: int = 0


@dataclass
class AnalysisResult:
    total_credits: float = 0.0
    total_debits: float = 0.0
    net_revenue: float = 0.0
    avg_monthly_credit: float = 0.0
    avg_monthly_debit: float = 0.0
    pos_total: float = 0.0
    pos_percentage: float = 0.0
    salary_transfers_total: float = 0.0
    salary_count: int = 0
    loan_payments_total: float = 0.0
    government_total: float = 0.0
    returned_cheques_count: int = 0
    bounced_percentage: float = 0.0
    total_cheques: int = 0
    months_covered: int = 0
    date_range_start: str = ""
    date_range_end: str = ""
    total_transactions: int = 0
    duplicate_count: int = 0
    outlier_count: int = 0
    internal_transfer_count: int = 0
    reversal_count: int = 0
    categories: dict[str, float] = field(default_factory=dict)
    monthly: list[MonthlyBreakdown] = field(default_factory=list)
    confidence_score: float = 0.0
    issues: list[str] = field(default_factory=list)
    risk_flags: list[RiskFlag] = field(default_factory=list)
    is_eligible: bool = False
    matched_entity: str | None = None
    offer_code: str | None = None
    rejection_reasons: list[str] = field(default_factory=list)
    # Revenue fluctuation for risk flags
    max_monthly_drop_pct: float = 0.0
    profit_ratio: float = 0.0


# ─── Helpers ───────────────────────────────────────────

def _categorize(description: str) -> str:
    desc_lower = description.lower().strip()
    for category, keywords in CATEGORY_RULES.items():
        if category == "other":
            continue
        for kw in keywords:
            if kw in desc_lower:
                return category
    return "other"


def _should_count(t: Transaction) -> bool:
    """Return True if this transaction should be counted in totals."""
    if t.is_duplicate:
        return False
    if t.is_internal_transfer:
        return False
    if t.reversal_pair_row is not None:
        return False
    return True


# ─── Main analysis ────────────────────────────────────

def analyze_transactions(parse_result: ParseResult) -> AnalysisResult:
    txns = parse_result.transactions
    result = AnalysisResult(
        total_transactions=parse_result.parsed_rows,
        duplicate_count=parse_result.duplicate_count,
        outlier_count=parse_result.outlier_count,
        internal_transfer_count=getattr(parse_result, 'internal_transfer_count', 0),
        reversal_count=getattr(parse_result, 'reversal_count', 0),
        months_covered=parse_result.months_covered,
        date_range_start=str(parse_result.date_range_start or ""),
        date_range_end=str(parse_result.date_range_end or ""),
        confidence_score=parse_result.confidence,
        issues=list(parse_result.issues),
    )

    if not txns:
        result.issues.append("لا توجد معاملات للتحليل")
        return result

    category_totals: dict[str, float] = defaultdict(float)
    monthly_data: dict[tuple[int, int], MonthlyBreakdown] = {}

    for t in txns:
        cat = _categorize(t.description)
        t.category = cat

        if not _should_count(t):
            continue

        result.total_credits += t.credit
        result.total_debits += t.debit
        category_totals[cat] += t.credit + t.debit

        if cat == "pos":
            result.pos_total += t.credit
        if cat == "salary_transfer":
            result.salary_transfers_total += t.debit
            result.salary_count += 1
        if cat == "loan_payment":
            result.loan_payments_total += t.debit
        if cat == "government":
            result.government_total += t.debit
        if cat == "returned_cheque":
            result.returned_cheques_count += 1
        if cat == "cheque":
            result.total_cheques += 1

        if t.date:
            key = (t.date.year, t.date.month)
            if key not in monthly_data:
                monthly_data[key] = MonthlyBreakdown(year=key[0], month=key[1])
            mb = monthly_data[key]
            mb.total_credit += t.credit
            mb.total_debit += t.debit
            mb.transaction_count += 1
            if cat == "pos":
                mb.pos_credit += t.credit
            if cat == "salary_transfer":
                mb.salary_transfers += t.debit
            if cat == "loan_payment":
                mb.loan_payments += t.debit
            if cat == "government":
                mb.government_payments += t.debit
            if cat == "returned_cheque":
                mb.returned_cheques += 1

    months = max(result.months_covered, 1)
    result.net_revenue = result.total_credits - result.total_debits
    result.avg_monthly_credit = result.total_credits / months
    result.avg_monthly_debit = result.total_debits / months

    if result.total_credits > 0:
        result.pos_percentage = round((result.pos_total / result.total_credits) * 100, 2)
        result.profit_ratio = result.net_revenue / result.total_credits
    else:
        result.profit_ratio = 0.0

    if result.total_cheques > 0:
        result.bounced_percentage = round(
            (result.returned_cheques_count / result.total_cheques) * 100, 2
        )

    result.categories = dict(category_totals)
    result.monthly = sorted(monthly_data.values(), key=lambda m: (m.year, m.month))

    # Compute max monthly drop
    if len(result.monthly) >= 2:
        max_drop = 0.0
        for i in range(1, len(result.monthly)):
            prev = result.monthly[i - 1].total_credit
            curr = result.monthly[i].total_credit
            if prev > 0:
                drop = (prev - curr) / prev
                if drop > max_drop:
                    max_drop = drop
        result.max_monthly_drop_pct = round(max_drop * 100, 2)

    # ── Generate Risk Flags ──────────────────────────
    result.risk_flags = _generate_risk_flags(result)

    logger.info(
        f"Analysis complete: credits={result.total_credits:,.0f}, "
        f"debits={result.total_debits:,.0f}, POS%={result.pos_percentage:.1f}%, "
        f"profit={result.profit_ratio:.1%}, risk_flags={len(result.risk_flags)}, "
        f"confidence={result.confidence_score:.2f}"
    )

    return result


# ─── Risk Flag Generator ──────────────────────────────

# Safety margins: if a value is within X% of the threshold, flag it
BORDERLINE_MARGIN = 0.15  # 15%


def _generate_risk_flags(analysis: AnalysisResult) -> list[RiskFlag]:
    """Generate risk flags for borderline figures."""
    flags: list[RiskFlag] = []

    # 1. Revenue fluctuation close to 20%
    if analysis.max_monthly_drop_pct > 0:
        if 15.0 <= analysis.max_monthly_drop_pct <= 25.0:
            flags.append(RiskFlag(
                code="REVENUE_FLUCTUATION",
                level=RiskLevel.MEDIUM,
                title_ar="تذبذب في الإيرادات",
                detail_ar=f"أقصى انخفاض شهري في الإيرادات: {analysis.max_monthly_drop_pct:.1f}% (الحد 20%)",
                value=analysis.max_monthly_drop_pct,
                threshold=20.0,
            ))
        elif analysis.max_monthly_drop_pct > 25.0:
            flags.append(RiskFlag(
                code="REVENUE_DROP_HIGH",
                level=RiskLevel.HIGH,
                title_ar="انخفاض حاد في الإيرادات",
                detail_ar=f"أقصى انخفاض شهري: {analysis.max_monthly_drop_pct:.1f}% (يتجاوز 25%)",
                value=analysis.max_monthly_drop_pct,
                threshold=20.0,
            ))

    # 2. Profit ratio close to 8%
    if analysis.total_credits > 0:
        profit_pct = analysis.profit_ratio * 100
        if 5.0 <= profit_pct < 10.0:
            flags.append(RiskFlag(
                code="PROFIT_BORDERLINE",
                level=RiskLevel.MEDIUM,
                title_ar="نسبة ربح قريبة من الحد الأدنى",
                detail_ar=f"نسبة الربح: {profit_pct:.1f}% (الحد الأدنى 8%)",
                value=profit_pct,
                threshold=8.0,
            ))
        elif profit_pct < 5.0:
            flags.append(RiskFlag(
                code="PROFIT_LOW",
                level=RiskLevel.HIGH,
                title_ar="نسبة ربح منخفضة",
                detail_ar=f"نسبة الربح: {profit_pct:.1f}% — أقل بكثير من الحد الأدنى 8%",
                value=profit_pct,
                threshold=8.0,
            ))

    # 3. Confidence score borderline
    if 0.70 <= analysis.confidence_score < 0.85:
        flags.append(RiskFlag(
            code="CONFIDENCE_BORDERLINE",
            level=RiskLevel.MEDIUM,
            title_ar="مستوى ثقة متوسط",
            detail_ar=f"مستوى الثقة: {analysis.confidence_score:.0%} — يستدعي مراجعة يدوية",
            value=analysis.confidence_score,
            threshold=0.85,
        ))
    elif analysis.confidence_score < 0.70:
        flags.append(RiskFlag(
            code="CONFIDENCE_LOW",
            level=RiskLevel.HIGH,
            title_ar="مستوى ثقة منخفض",
            detail_ar=f"مستوى الثقة: {analysis.confidence_score:.0%} — بيانات غير كافية",
            value=analysis.confidence_score,
            threshold=0.70,
        ))

    # 4. Missing months in data
    if analysis.months_covered > 0 and len(analysis.monthly) > 0:
        sorted_m = sorted(analysis.monthly, key=lambda m: (m.year, m.month))
        gaps = 0
        for i in range(1, len(sorted_m)):
            py, pm = sorted_m[i-1].year, sorted_m[i-1].month
            ey, em = (py, pm + 1) if pm < 12 else (py + 1, 1)
            if (sorted_m[i].year, sorted_m[i].month) != (ey, em):
                gaps += 1
        if gaps > 0:
            flags.append(RiskFlag(
                code="DATA_GAPS",
                level=RiskLevel.MEDIUM if gaps < 2 else RiskLevel.HIGH,
                title_ar="فجوات في البيانات الشهرية",
                detail_ar=f"عدد الفجوات: {gaps} شهر مفقود في التسلسل",
                value=gaps,
                threshold=0,
            ))

    # 5. High duplicate ratio
    if analysis.total_transactions > 0:
        dup_ratio = analysis.duplicate_count / analysis.total_transactions
        if dup_ratio > 0.10:
            flags.append(RiskFlag(
                code="HIGH_DUPLICATES",
                level=RiskLevel.MEDIUM,
                title_ar="نسبة عالية من المعاملات المكررة",
                detail_ar=f"نسبة المكرر: {dup_ratio:.0%} ({analysis.duplicate_count} معاملة)",
                value=dup_ratio * 100,
                threshold=10.0,
            ))

    # 6. Bounced cheques
    if analysis.bounced_percentage > 5:
        flags.append(RiskFlag(
            code="BOUNCED_CHEQUES",
            level=RiskLevel.HIGH,
            title_ar="نسبة شيكات مرتجعة عالية",
            detail_ar=f"نسبة الشيكات المرتجعة: {analysis.bounced_percentage:.1f}%",
            value=analysis.bounced_percentage,
            threshold=5.0,
        ))

    # 7. Very low monthly average
    if analysis.avg_monthly_credit > 0 and analysis.avg_monthly_credit < 50_000:
        flags.append(RiskFlag(
            code="LOW_MONTHLY_REVENUE",
            level=RiskLevel.LOW,
            title_ar="متوسط إيرادات شهرية منخفض",
            detail_ar=f"متوسط الإيرادات الشهرية: {analysis.avg_monthly_credit:,.0f} ريال",
            value=analysis.avg_monthly_credit,
            threshold=50_000,
        ))

    return flags
