"""
Analysis API — File upload (CR + Bank Statement), pre-filter, trigger analysis, get status.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime

import aiofiles
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User, UserRole
from app.models.case import Case, CaseStage, CaseStageHistory
from app.models.audit import AuditLog, AuditAction, Notification, NotificationType
from app.core.rbac import get_current_user
from app.core.dependencies import validate_excel_file, validate_cr_file
from app.schemas.case import CaseResponse, AnalysisResultSchema
from app.engine.rule_engine import pre_filter_entities, calculate_required_bs_months
from app.services.ai_service import analyze_cr_document, generate_bs_summary, analyze_bs_pdf
import asyncio

settings = get_settings()
router = APIRouter(prefix="/analysis", tags=["analysis"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")


async def _notify_partner_docs_required(db: AsyncSession, case: Case, required_docs: list[str]):
    """Send automatic notification to partner with AI-determined required documents."""
    if not required_docs:
        docs_str = "المستندات المطلوبة للتمويل"
    else:
        docs_str = "، ".join(required_docs[:5])  # first 5 docs to keep message short
        if len(required_docs) > 5:
            docs_str += f" وأخرى ({len(required_docs)} مستند)"
    notif = Notification(
        user_id=case.partner_id,
        notification_type=NotificationType.completion_requested,
        title=f"طلبك {case.display_id} مؤهل — يرجى رفع المستندات",
        message=f"تهانينا! تم قبول طلبك مبدئياً. يرجى رفع: {docs_str}",
        case_id=case.id,
    )
    db.add(notif)




async def _run_cr_ai_background(case_id_str: str, file_bytes: bytes, filename: str):
    """Background task: run AI OCR on CR and persist results to DB."""
    from app.database import async_session
    from app.models.case import Case
    from sqlalchemy import select
    from datetime import date as _date
    try:
        ai_data = await analyze_cr_document(file_bytes, filename)
        if not ai_data:
            return
        async with async_session() as db:
            result = await db.execute(select(Case).where(Case.id == case_id_str))
            case = result.scalar_one_or_none()
            if not case:
                return
            if ai_data.get("company_name"):
                case.company_name = ai_data["company_name"]
            if ai_data.get("registration_number"):
                case.registration_number = ai_data["registration_number"]
            if ai_data.get("issue_date"):
                case.issue_date = ai_data["issue_date"]
                try:
                    issue = _date.fromisoformat(ai_data["issue_date"])
                    today = _date.today()
                    months = (today.year - issue.year) * 12 + (today.month - issue.month)
                    if today.day < issue.day:
                        months -= 1
                    case.age_in_months = max(0, months)
                except Exception:
                    pass
            if ai_data.get("entity_type"):
                case.entity_type = ai_data["entity_type"]
            if ai_data.get("activity"):
                case.activity = ai_data["activity"]
            await db.commit()
            logger.info(f"CR AI background task done for case {case_id_str}")
    except Exception as e:
        logger.error(f"CR AI background task failed: {e}")


async def _save_file(file: UploadFile, subfolder: str) -> tuple[str, str]:
    """Save uploaded file and return (path, filename)."""
    os.makedirs(os.path.join(UPLOAD_DIR, subfolder), exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "bin"
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD_DIR, subfolder, unique_name)

    async with aiofiles.open(path, "wb") as f:
        content = await file.read()
        await f.write(content)

    return path, file.filename or unique_name


def _generate_display_id() -> str:
    """Generate a human-readable display ID."""
    import random
    return f"JBZ-{random.randint(10000, 99999)}"


# ─── Create new case manually (no CR file) ────────────

@router.post("/create-manual", status_code=201)
async def create_manual_case(
    facility_type: str = "pos",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new case without uploading a CR file (manual data entry)."""
    if current_user.role != UserRole.partner:
        raise HTTPException(403, "فقط الشركاء يمكنهم إنشاء الطلبات")
    if facility_type not in ("pos", "cash", "fleet"):
        raise HTTPException(422, "نوع التسهيلات غير صالح")

    case = Case(
        display_id=_generate_display_id(),
        partner_id=current_user.id,
        facility_type=facility_type,
        stage=CaseStage.analyzing,
    )
    db.add(case)
    await db.flush()

    history = CaseStageHistory(
        case_id=case.id,
        stage=CaseStage.analyzing,
        updated_by=current_user.id,
        updated_by_role=current_user.role.value,
        updated_by_name=current_user.name,
        note="تم إنشاء الطلب بالإدخال اليدوي",
    )
    db.add(history)

    audit = AuditLog(
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role.value,
        action=AuditAction.case_created,
        case_id=case.id,
        details={"manual": True},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(case)

    return {
        "case_id": str(case.id),
        "display_id": case.display_id,
        "stage": case.stage.value,
        "message": "تم إنشاء الطلب بالإدخال اليدوي",
    }


# ─── Create new case + upload CR ──────────────────────

@router.post("/upload-cr", status_code=201)
async def upload_cr(
    file: UploadFile = File(...),
    facility_type: str = "pos",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload Commercial Registration document and create a new case."""
    if current_user.role != UserRole.partner:
        raise HTTPException(403, "فقط الشركاء يمكنهم رفع السجل التجاري")

    if facility_type not in ("pos", "cash", "fleet"):
        raise HTTPException(422, "نوع التسهيلات غير صالح. الخيارات: pos, cash, fleet")

    await validate_cr_file(file)

    # Read bytes before saving (needed for AI OCR)
    file_content = await file.read()
    await file.seek(0)

    path, filename = await _save_file(file, "cr")

    case = Case(
        display_id=_generate_display_id(),
        partner_id=current_user.id,
        cr_file_path=path,
        cr_file_name=filename,
        facility_type=facility_type,
        stage=CaseStage.analyzing,
    )
    db.add(case)
    await db.flush()

    # Stage history
    history = CaseStageHistory(
        case_id=case.id,
        stage=CaseStage.analyzing,
        updated_by=current_user.id,
        updated_by_role=current_user.role.value,
        updated_by_name=current_user.name,
        note="تم إنشاء الطلب ورفع السجل التجاري",
    )
    db.add(history)

    # Audit
    audit = AuditLog(
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role.value,
        action=AuditAction.case_created,
        case_id=case.id,
        details={"cr_file": filename},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(case)

    # Fire AI OCR as background task — upload returns instantly
    asyncio.create_task(_run_cr_ai_background(str(case.id), file_content, filename))

    return {
        "case_id": str(case.id),
        "display_id": case.display_id,
        "stage": case.stage.value,
        "message": "تم رفع السجل التجاري بنجاح",
        "ai_extracted": {},
    }


# ─── Update CR info (from partner form) ──────────────

@router.patch("/{case_id}/cr-info")
async def update_cr_info(
    case_id: uuid.UUID,
    company_name: str = "",
    registration_number: str = "",
    entity_type: str = "",
    issue_date: str = "",
    age_in_months: int = 0,
    activity: str = "",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update CR analysis results (from frontend form or OCR pipeline)."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    if current_user.role == UserRole.partner and case.partner_id != current_user.id:
        raise HTTPException(403, "ليس لديك صلاحية")

    case.company_name = company_name
    case.registration_number = registration_number
    case.entity_type = entity_type
    case.issue_date = issue_date
    case.age_in_months = age_in_months
    if activity:
        case.activity = activity

    await db.commit()
    return {"status": "updated"}


# ─── Upload basic document ────────────────────────────

@router.post("/{case_id}/upload-basic-doc")
async def upload_basic_doc(
    case_id: uuid.UUID,
    doc_name: str = Query(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a basic document (ID, IBAN, national address).
    Stored in supplementary_docs column — same mechanism as CR/BS supplementary docs,
    completely isolated from analysis_result so the analysis engine never overwrites them.
    """
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")
    if current_user.role == UserRole.partner and case.partner_id != current_user.id:
        raise HTTPException(403, "ليس لديك صلاحية")

    # Save to docs/{case_id} — same folder used by the supplementary-doc download endpoint
    subfolder = f"docs/{case_id}"
    os.makedirs(os.path.join(UPLOAD_DIR, subfolder), exist_ok=True)
    ext = (file.filename or "bin").rsplit(".", 1)[-1] if "." in (file.filename or "") else "bin"
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, subfolder, unique_name)
    content = await file.read()
    async with aiofiles.open(file_path, "wb") as out:
        await out.write(content)

    original_name = file.filename or unique_name

    # Re-fetch with row lock + populate_existing to bypass the ORM identity map
    result2 = await db.execute(
        select(Case).where(Case.id == case_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    case = result2.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    # Write to supplementary_docs — not analysis_result, so analysis can never overwrite it
    existing_docs = list(case.supplementary_docs or [])
    # If partner re-uploads the same doc, replace the old entry
    existing_docs = [d for d in existing_docs
                     if not (d.get("type") == "basic_doc" and d.get("label") == doc_name)]
    existing_docs.append({
        "type": "basic_doc",
        "label": doc_name,
        "stored_name": unique_name,
        "original_name": original_name,
        "size": len(content),
        "uploaded_at": datetime.utcnow().isoformat(),
    })
    case.supplementary_docs = existing_docs
    await db.commit()
    return {"status": "ok", "filename": original_name}


# ─── Save financial data ──────────────────────────────

@router.patch("/{case_id}/financial")
async def save_financial_data(
    case_id: uuid.UUID,
    total_credit: float = 0.0,
    total_debit: float = 0.0,
    pos_sales: float = 0.0,
    other_income: float = 0.0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save partner-entered financial data into analysis_result JSON."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")
    if current_user.role == UserRole.partner and case.partner_id != current_user.id:
        raise HTTPException(403, "ليس لديك صلاحية")

    existing = dict(case.analysis_result or {})
    existing["total_credit"] = total_credit
    existing["total_debit"] = total_debit
    existing["pos_sales"] = pos_sales
    existing["other_income"] = other_income
    case.analysis_result = existing
    await db.commit()
    return {"status": "ok"}


# ─── Update partner questions ─────────────────────────

class QuestionsBody(BaseModel):
    has_pos: bool
    has_invoices: bool = False
    partner_count: int  # 1 or 2+
    is_saudi: bool


@router.patch("/{case_id}/questions")
async def update_questions(
    case_id: uuid.UUID,
    body: QuestionsBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save partner answers to mandatory questions (POS, partners, nationality)."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    if current_user.role == UserRole.partner and case.partner_id != current_user.id:
        raise HTTPException(403, "ليس لديك صلاحية")

    case.has_pos = body.has_pos
    case.has_invoices = body.has_invoices
    case.partner_count = body.partner_count
    case.is_saudi = body.is_saudi

    await db.commit()
    return {"status": "updated"}


# ─── Pre-filter entities (before bank statement) ──────

@router.post("/{case_id}/pre-filter")
async def run_pre_filter(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Run Smart Routing pre-filter using CR data + questions.
    Determines which entities/products are possible BEFORE requesting bank statement.
    If none → reject immediately without bank statement.
    """
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    if current_user.role == UserRole.partner and case.partner_id != current_user.id:
        raise HTTPException(403, "ليس لديك صلاحية")

    if not case.facility_type:
        raise HTTPException(400, "لم يتم تحديد نوع التسهيلات")

    # Run pre-filter
    pf = await pre_filter_entities(
        db=db,
        facility_type=case.facility_type,
        age_months=case.age_in_months,
        entity_type=case.entity_type,
        activity=case.activity,
        has_pos=case.has_pos or False,
        has_invoices=case.has_invoices or False,
        partner_count=case.partner_count,
        is_saudi=case.is_saudi if case.is_saudi is not None else True,
    )

    # Calculate required bank statement months
    required_bs = calculate_required_bs_months(case.age_in_months)

    # Store results on case
    eligible_codes = [p["product_code"] for p in pf.eligible_products]
    case.pre_filter_passed = eligible_codes
    case.required_bs_months = required_bs

    if pf.has_eligible and required_bs > 0:
        # Has eligible products → set first product as current
        case.current_product_code = eligible_codes[0]
    else:
        # No eligible products or age too low → reject
        case.is_eligible = False
        case.stage = CaseStage.rejected
        case.result_summary = "غير مؤهل حالياً — لا توجد جهة تمويل مناسبة"

        # Audit log
        audit = AuditLog(
            user_id=current_user.id,
            user_name=current_user.name,
            user_role=current_user.role.value,
            action=AuditAction.analysis_completed,
            case_id=case.id,
            details={
                "result": "rejected_pre_filter",
                "reason": "no_eligible_entity",
                "routing_log": pf.rejection_log,
            },
        )
        db.add(audit)

    await db.commit()

    return {
        "case_id": str(case.id),
        "has_eligible": pf.has_eligible,
        "eligible_count": len(pf.eligible_products),
        "required_bs_months": required_bs,
        "rejected": not pf.has_eligible or required_bs == 0,
    }


# ─── Upload bank statement + trigger analysis ────────

@router.post("/{case_id}/upload-bs")
async def upload_bank_statement(
    case_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload bank statement Excel and enqueue analysis."""
    if current_user.role != UserRole.partner:
        raise HTTPException(403, "فقط الشركاء يمكنهم رفع كشف الحساب")

    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    if case.partner_id != current_user.id:
        raise HTTPException(403, "ليس لديك صلاحية لهذا الطلب")

    await validate_excel_file(file)

    path, filename = await _save_file(file, "bs")
    case.bs_file_path = path
    case.bs_file_name = filename
    case.analysis_progress = 0

    # Audit
    audit = AuditLog(
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role.value,
        action=AuditAction.file_uploaded,
        case_id=case.id,
        details={"bs_file": filename},
    )
    db.add(audit)

    await db.commit()

    # Enqueue analysis job
    try:
        from app.worker import get_redis_pool

        # Read file bytes for worker
        async with aiofiles.open(path, "rb") as f:
            file_bytes = await f.read()

        redis = await get_redis_pool()
        required_months = max(case.age_in_months, 6) if case.age_in_months else 6
        if required_months > 12:
            required_months = 12

        await redis.enqueue_job(
            "process_bank_statement",
            str(case.id),
            file_bytes,
            required_months,
        )

        # Update audit
        audit2 = AuditLog(
            user_id=current_user.id,
            user_name=current_user.name,
            user_role=current_user.role.value,
            action=AuditAction.analysis_started,
            case_id=case.id,
        )
        db.add(audit2)
        await db.commit()

        return {
            "case_id": str(case.id),
            "status": "queued",
            "message": "تم رفع كشف الحساب وبدأ التحليل",
        }

    except Exception as e:
        # If Redis is not available, run analysis inline (fallback)
        from app.engine import parse_bank_statement
        from app.engine.analyzer import analyze_transactions
        from app.engine.validator import validate_analysis
        from app.engine.rule_engine import match_entity, generate_offer_code
        from loguru import logger

        logger.warning(f"Redis unavailable, running analysis inline: {e}")

        async with aiofiles.open(path, "rb") as f:
            file_bytes = await f.read()

        # ── PDF bank statement → AI analysis ─────────────────────────────────
        is_pdf_bs = (case.bs_file_name or "").lower().endswith(".pdf")
        if is_pdf_bs:
            logger.info(f"PDF bank statement for case {case.id} — running AI analysis")
            case.analysis_progress = 20
            await db.commit()

            ai_bs = await analyze_bs_pdf(file_bytes, case.bs_file_name or "statement.pdf")

            if not ai_bs:
                # AI extraction failed → manual review fallback
                case.is_eligible = False
                case.stage = CaseStage.completing_request
                case.result_summary = ""
                case.analysis_progress = 100
                _prev_ar = case.analysis_result or {}
                case.analysis_result = {
                    "pdf_manual_review": True, "required_docs": [],
                    "total_credit": _prev_ar.get("total_credit"),
                    "total_debit": _prev_ar.get("total_debit"),
                    "pos_sales": _prev_ar.get("pos_sales"),
                    "other_income": _prev_ar.get("other_income"),
                }
                case.last_stage_change_at = datetime.utcnow()
                await db.commit()
                return {
                    "case_id": str(case.id),
                    "status": "completed",
                    "is_eligible": False,
                    "result_summary": case.result_summary,
                    "message": "PDF بانتظار المراجعة اليدوية",
                }

            # Build AnalysisResult from AI-extracted data
            from app.engine.analyzer import AnalysisResult, MonthlyBreakdown, RiskFlag

            monthly_list = []
            for m in ai_bs.get("monthly", []):
                monthly_list.append(MonthlyBreakdown(
                    year=m.get("year", 0),
                    month=m.get("month", 0),
                    total_credit=float(m.get("total_credit", 0)),
                    total_debit=float(m.get("total_debit", 0)),
                    pos_credit=float(m.get("pos_credit", 0)),
                    returned_cheques=int(m.get("returned_cheques", 0)),
                ))

            total_credits = float(ai_bs.get("total_credits", 0))
            total_debits = float(ai_bs.get("total_debits", 0))
            pos_total = float(ai_bs.get("pos_total", 0))
            months_covered = int(ai_bs.get("months_covered", 1)) or 1

            analysis = AnalysisResult(
                total_credits=total_credits,
                total_debits=total_debits,
                net_revenue=total_credits - total_debits,
                avg_monthly_credit=total_credits / months_covered,
                avg_monthly_debit=total_debits / months_covered,
                pos_total=pos_total,
                pos_percentage=(pos_total / total_credits * 100) if total_credits else 0,
                returned_cheques_count=int(ai_bs.get("returned_cheques_count", 0)),
                bounced_percentage=0.0,
                months_covered=months_covered,
                total_transactions=0,
                max_monthly_drop_pct=float(ai_bs.get("max_monthly_drop_pct", 0)),
                profit_ratio=float(ai_bs.get("profit_ratio", 0)),
                confidence_score=float(ai_bs.get("confidence_score", 0.5)),
                monthly=monthly_list,
                issues=[],
                risk_flags=[],
            )
            case.analysis_progress = 50

            eligible_codes = case.pre_filter_passed or []
            validation = validate_analysis(
                analysis,
                eligible_entity_count=len(eligible_codes),
                docs_complete=bool(case.cr_file_path and case.bs_file_path),
            )
            case.analysis_progress = 70

            case.risk_flags = [
                {
                    "code": f.code, "level": f.level,
                    "title_ar": f.title_ar, "detail_ar": f.detail_ar,
                    "value": f.value, "threshold": f.threshold,
                }
                for f in analysis.risk_flags
            ]
            case.risk_flag_count = validation.risk_flag_count
            case.has_high_risk = validation.has_high_risk
            case.validation_recommendation = validation.recommendation

            matched_rule, routing_log = await match_entity(
                db, analysis, case.age_in_months, case.entity_type,
                eligible_product_codes=eligible_codes if eligible_codes else None,
            )

            if not validation.is_valid:
                case.stage = CaseStage.completing_request
                case.is_eligible = False
                case.result_summary = "البيانات تحتاج مراجعة إضافية"
            elif validation.recommendation == "auto_approve" and matched_rule:
                offer_code = await generate_offer_code(db, matched_rule.offer_code_prefix)
                case.is_eligible = True
                case.entity_name = matched_rule.entity_name
                case.offer_code = offer_code
                case.stage = CaseStage.completing_request
                case.result_summary = f"مؤهل (موافقة تلقائية) — كود العرض: {offer_code}"
            elif matched_rule:
                offer_code = await generate_offer_code(db, matched_rule.offer_code_prefix)
                case.is_eligible = True
                case.entity_name = matched_rule.entity_name
                case.offer_code = offer_code
                case.stage = CaseStage.completing_request
                case.result_summary = f"مؤهل (بانتظار المراجعة) — كود العرض: {offer_code}"
            else:
                case.is_eligible = False
                case.stage = CaseStage.completing_request
                case.result_summary = "غير مؤهل حالياً"

            case.confidence_score = analysis.confidence_score
            analysis_result_dict = {
                "total_credits": analysis.total_credits,
                "total_debits": analysis.total_debits,
                "avg_monthly_credit": analysis.avg_monthly_credit,
                "avg_monthly_debit": analysis.avg_monthly_debit,
                "net_revenue": analysis.net_revenue,
                "pos_total": analysis.pos_total,
                "pos_percentage": analysis.pos_percentage,
                "returned_cheques_count": analysis.returned_cheques_count,
                "months_covered": analysis.months_covered,
                "confidence_score": analysis.confidence_score,
                "is_eligible": matched_rule is not None and validation.is_valid,
                "matched_entity": matched_rule.entity_name if matched_rule else None,
                "rejection_reasons": analysis.issues,
                "issues": analysis.issues,
                "required_docs": matched_rule.required_docs if matched_rule and matched_rule.required_docs else [],
                "smart_routing_log": routing_log,
                "risk_flags": [
                    {"code": f.code, "level": f.level, "title_ar": f.title_ar, "detail_ar": f.detail_ar}
                    for f in analysis.risk_flags
                ],
                "recommendation": validation.recommendation,
                "max_monthly_drop_pct": analysis.max_monthly_drop_pct,
                "profit_ratio": analysis.profit_ratio,
                "pdf_source": True,
                "ai_extracted": True,
                "date_range_start": ai_bs.get("date_range_start"),
                "date_range_end": ai_bs.get("date_range_end"),
            }
            try:
                ai_summary = await generate_bs_summary(analysis_result_dict)
                if ai_summary:
                    analysis_result_dict["ai_summary"] = ai_summary
            except Exception as _ai_err:
                logger.warning(f"BS AI summary skipped: {_ai_err}")

            # Preserve partner-entered fields that were saved before analysis ran
            _prev = case.analysis_result or {}
            for _k in ("total_credit", "total_debit", "pos_sales", "other_income"):
                if _k in _prev:
                    analysis_result_dict[_k] = _prev[_k]
            case.analysis_result = analysis_result_dict
            case.analysis_progress = 100
            case.last_stage_change_at = datetime.utcnow()
            # Auto-notify partner about required documents
            if case.is_eligible and matched_rule:
                await _notify_partner_docs_required(db, case, matched_rule.required_docs or [])
            await db.commit()
            await db.refresh(case)
            return {
                "case_id": str(case.id),
                "status": "completed",
                "is_eligible": case.is_eligible,
                "result_summary": case.result_summary,
                "message": "اكتمل تحليل PDF بالذكاء الاصطناعي",
            }

        required_months = max(case.age_in_months, 6) if case.age_in_months else 6
        if required_months > 12:
            required_months = 12

        parse_result = parse_bank_statement(file_bytes, required_months)
        case.analysis_progress = 30

        analysis = analyze_transactions(parse_result)
        case.analysis_progress = 60

        # Use pre-filtered product codes if available
        eligible_codes = case.pre_filter_passed or []
        validation = validate_analysis(
            analysis,
            eligible_entity_count=len(eligible_codes),
            docs_complete=bool(case.cr_file_path and case.bs_file_path),
        )
        case.analysis_progress = 75

        # Store risk flags on case
        case.risk_flags = [
            {
                "code": f.code, "level": f.level,
                "title_ar": f.title_ar, "detail_ar": f.detail_ar,
                "value": f.value, "threshold": f.threshold,
            }
            for f in analysis.risk_flags
        ]
        case.risk_flag_count = validation.risk_flag_count
        case.has_high_risk = validation.has_high_risk
        case.validation_recommendation = validation.recommendation

        matched_rule, routing_log = await match_entity(
            db, analysis, case.age_in_months, case.entity_type,
            eligible_product_codes=eligible_codes if eligible_codes else None,
        )

        if not validation.is_valid:
            case.stage = CaseStage.completing_request
            case.is_eligible = False
            case.result_summary = "البيانات تحتاج مراجعة إضافية"
        elif validation.recommendation == "auto_approve" and matched_rule:
            offer_code = await generate_offer_code(db, matched_rule.offer_code_prefix)
            case.is_eligible = True
            case.entity_name = matched_rule.entity_name
            case.offer_code = offer_code
            case.stage = CaseStage.completing_request
            case.result_summary = f"مؤهل (موافقة تلقائية) — كود العرض: {offer_code}"
        elif matched_rule:
            offer_code = await generate_offer_code(db, matched_rule.offer_code_prefix)
            case.is_eligible = True
            case.entity_name = matched_rule.entity_name
            case.offer_code = offer_code
            case.stage = CaseStage.completing_request
            case.result_summary = f"مؤهل (بانتظار المراجعة) — كود العرض: {offer_code}"
        else:
            case.is_eligible = False
            case.stage = CaseStage.completing_request
            case.result_summary = "غير مؤهل حالياً"

        case.confidence_score = analysis.confidence_score
        analysis_result_dict = {
            "total_credits": analysis.total_credits,
            "total_debits": analysis.total_debits,
            "avg_monthly_credit": analysis.avg_monthly_credit,
            "avg_monthly_debit": analysis.avg_monthly_debit,
            "net_revenue": analysis.net_revenue,
            "pos_total": analysis.pos_total,
            "pos_percentage": analysis.pos_percentage,
            "salary_transfers_total": analysis.salary_transfers_total,
            "returned_cheques_count": analysis.returned_cheques_count,
            "bounced_percentage": analysis.bounced_percentage,
            "months_covered": analysis.months_covered,
            "total_transactions": analysis.total_transactions,
            "confidence_score": analysis.confidence_score,
            "is_eligible": matched_rule is not None and validation.is_valid,
            "matched_entity": matched_rule.entity_name if matched_rule else None,
            "rejection_reasons": analysis.issues,
            "issues": analysis.issues,
            "required_docs": matched_rule.required_docs if matched_rule and matched_rule.required_docs else [],
            "smart_routing_log": routing_log,
            "risk_flags": [
                {"code": f.code, "level": f.level, "title_ar": f.title_ar, "detail_ar": f.detail_ar}
                for f in analysis.risk_flags
            ],
            "recommendation": validation.recommendation,
            "max_monthly_drop_pct": analysis.max_monthly_drop_pct,
            "profit_ratio": analysis.profit_ratio,
        }
        # AI-generated Arabic summary (GPT-4o-mini — cheap)
        try:
            ai_summary = await generate_bs_summary(analysis_result_dict)
            if ai_summary:
                analysis_result_dict["ai_summary"] = ai_summary
        except Exception as _ai_err:
            logger.warning(f"BS AI summary skipped: {_ai_err}")

        # Preserve partner-entered fields that were saved before analysis ran
        _prev = case.analysis_result or {}
        for _k in ("total_credit", "total_debit", "pos_sales", "other_income"):
            if _k in _prev:
                analysis_result_dict[_k] = _prev[_k]
        case.analysis_result = analysis_result_dict
        case.analysis_progress = 100
        case.last_stage_change_at = datetime.utcnow()
        # Auto-notify partner about required documents
        if case.is_eligible and matched_rule:
            await _notify_partner_docs_required(db, case, matched_rule.required_docs or [])
        await db.commit()
        await db.refresh(case)

        return {
            "case_id": str(case.id),
            "status": "completed",
            "is_eligible": case.is_eligible,
            "result_summary": case.result_summary,
            "message": "اكتمل التحليل (معالجة مباشرة)",
        }


# ─── AI: Analyze CR document (standalone) ────────────

@router.post("/{case_id}/ai-analyze-cr")
async def ai_analyze_cr(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns AI-extracted CR fields.
    - If background task already ran → returns cached DB data instantly.
    - If background task still running → polls DB up to 20s then falls back to running AI itself.
    """
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    if current_user.role == UserRole.partner and case.partner_id != current_user.id:
        raise HTTPException(403, "ليس لديك صلاحية")

    if not case.cr_file_path or not os.path.exists(case.cr_file_path):
        raise HTTPException(400, "لم يتم رفع السجل التجاري بعد")

    def _case_has_ai_data(c) -> bool:
        return bool(c.company_name or c.issue_date or c.registration_number)

    # ── Poll DB for background task result (max 20s, every 1.5s) ──
    if not _case_has_ai_data(case):
        for _ in range(13):
            await asyncio.sleep(1.5)
            await db.refresh(case)
            if _case_has_ai_data(case):
                break

    # ── If background task finished, return cached data ──
    if _case_has_ai_data(case):
        ai_data = {
            "company_name": case.company_name or "",
            "registration_number": case.registration_number or "",
            "issue_date": case.issue_date or "",
            "entity_type": case.entity_type or "",
            "activity": getattr(case, "activity", "") or "",
        }
        return {
            "case_id": str(case.id),
            "ai_extracted": ai_data,
            "age_in_months": case.age_in_months,
            "message": "تم استخراج بيانات السجل التجاري بنجاح",
        }

    # ── Fallback: run AI directly (background task timed out) ──
    async with aiofiles.open(case.cr_file_path, "rb") as f:
        file_bytes = await f.read()

    ai_data = await analyze_cr_document(file_bytes, case.cr_file_name or "cr.pdf")
    if not ai_data:
        raise HTTPException(503, "فشل تحليل الذكاء الاصطناعي — تحقق من OPENAI_API_KEY")

    if ai_data.get("company_name"):
        case.company_name = ai_data["company_name"]
    if ai_data.get("registration_number"):
        case.registration_number = ai_data["registration_number"]
    if ai_data.get("issue_date"):
        case.issue_date = ai_data["issue_date"]
        try:
            from datetime import date as _date
            issue = _date.fromisoformat(ai_data["issue_date"])
            today = _date.today()
            months = (today.year - issue.year) * 12 + (today.month - issue.month)
            if today.day < issue.day:
                months -= 1
            case.age_in_months = max(0, months)
        except Exception:
            pass
    if ai_data.get("entity_type"):
        case.entity_type = ai_data["entity_type"]
    if ai_data.get("activity"):
        case.activity = ai_data["activity"]

    await db.commit()

    return {
        "case_id": str(case.id),
        "ai_extracted": ai_data,
        "age_in_months": case.age_in_months,
        "message": "تم استخراج بيانات السجل التجاري بنجاح",
    }


# ─── AI: Summarize analysis result ───────────────────

@router.post("/{case_id}/ai-summarize")
async def ai_summarize_result(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a fresh AI Arabic narrative summary of the analysis result.
    Uses GPT-4o-mini — very cheap (~$0.0002 per call).
    """
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    if current_user.role == UserRole.partner and case.partner_id != current_user.id:
        raise HTTPException(403, "ليس لديك صلاحية")

    if not case.analysis_result:
        raise HTTPException(400, "لم يكتمل التحليل بعد")

    summary = await generate_bs_summary(case.analysis_result)
    if not summary:
        raise HTTPException(503, "فشل توليد الملخص — تحقق من OPENAI_API_KEY")

    # Persist into analysis_result
    updated = dict(case.analysis_result)
    updated["ai_summary"] = summary
    case.analysis_result = updated
    await db.commit()

    return {"case_id": str(case.id), "ai_summary": summary}


# ─── Get analysis status/progress ────────────────────

@router.get("/{case_id}/status")
async def analysis_status(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    if current_user.role == UserRole.partner and case.partner_id != current_user.id:
        raise HTTPException(403, "ليس لديك صلاحية")

    return {
        "case_id": str(case.id),
        "stage": case.stage.value,
        "analysis_progress": case.analysis_progress,
        "is_eligible": case.is_eligible,
        "confidence_score": case.confidence_score,
        "result_summary": case.result_summary,
        "offer_code": case.offer_code,
    }


# ─── Get full analysis result ────────────────────────

@router.get("/{case_id}/result")
async def analysis_result(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    if current_user.role == UserRole.partner and case.partner_id != current_user.id:
        raise HTTPException(403, "ليس لديك صلاحية")

    if not case.analysis_result:
        raise HTTPException(400, "لم يكتمل التحليل بعد")

    response = dict(case.analysis_result)

    # Hide entity name & smart routing log unless owner/supervisor
    if current_user.role not in (UserRole.owner, UserRole.supervisor):
        response.pop("matched_entity", None)
        response.pop("smart_routing_log", None)

    # Always hide smart_routing_log from partner
    if current_user.role == UserRole.partner:
        response.pop("smart_routing_log", None)

    return response


# ─── Audit log (supervisor/owner) ────────────────────

@router.get("/{case_id}/audit")
async def case_audit_log(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in (UserRole.supervisor, UserRole.owner):
        raise HTTPException(403, "ليس لديك صلاحية لعرض سجل التدقيق")

    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.case_id == case_id)
        .order_by(AuditLog.timestamp.desc())
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "user_name": l.user_name,
            "user_role": l.user_role,
            "action": l.action.value,
            "details": l.details,
            "timestamp": l.timestamp.isoformat(),
            "ip_address": l.ip_address,
        }
        for l in logs
    ]


# ─── Supplementary document upload (completing_request stage) ─

@router.post("/{case_id}/upload-documents", status_code=200)
async def upload_supplementary_documents(
    case_id: uuid.UUID,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload supplementary documents for a case in completing_request stage.
    After saving, runs AI summary and advances stage to fee_contract_signed.
    """
    from app.services.ai_service import summarize_supplementary_docs
    from app.models.case import STAGES_ORDER

    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    if current_user.role == UserRole.partner and str(case.partner_id) != str(current_user.id):
        raise HTTPException(403, "ليس لديك صلاحية لهذا الطلب")

    if not files:
        raise HTTPException(400, "يجب رفع ملف واحد على الأقل")

    saved_files = []
    uploaded_names = []

    for f in files:
        content = await f.read()
        if len(content) == 0:
            continue  # skip empty files
        if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(413, f"الملف {f.filename} يتجاوز الحد المسموح ({settings.MAX_FILE_SIZE_MB}MB)")

        allowed = (".pdf", ".png", ".jpg", ".jpeg", ".xlsx", ".xls", ".heic", ".webp")
        ext = (f.filename or "").rsplit(".", 1)[-1].lower() if f.filename else ""
        if f".{ext}" not in allowed:
            raise HTTPException(400, f"نوع الملف {f.filename} غير مسموح")

        subfolder = f"docs/{case_id}"
        os.makedirs(os.path.join(UPLOAD_DIR, subfolder), exist_ok=True)
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        path = os.path.join(UPLOAD_DIR, subfolder, unique_name)

        async with aiofiles.open(path, "wb") as out:
            await out.write(content)

        # Use original filename (without extension) as display label
        label = (f.filename or unique_name).rsplit(".", 1)[0]
        saved_files.append({
            "original_name": f.filename,
            "label": label,
            "stored_name": unique_name,
            "size": len(content),
            "uploaded_at": datetime.utcnow().isoformat(),
        })
        uploaded_names.append(f.filename or unique_name)

    if not saved_files:
        raise HTTPException(400, "لم يتم حفظ أي ملف")

    # Merge with existing docs
    existing_docs = list(case.supplementary_docs or [])
    existing_docs.extend(saved_files)
    case.supplementary_docs = existing_docs

    # ── Look for bank statement PDF and run full AI analysis ─────────────────
    bs_analysis_extra = ""
    bs_keywords = ["كشف", "حساب", "bank", "statement", "bs_"]
    for f_info in saved_files:
        label_l = f_info["label"].lower()
        fname_l = (f_info["original_name"] or "").lower()
        is_bs = any(kw in label_l or kw in fname_l for kw in bs_keywords)
        is_pdf = f_info["stored_name"].lower().endswith(".pdf")
        if is_bs and is_pdf:
            bs_path = os.path.join(UPLOAD_DIR, f"docs/{case_id}", f_info["stored_name"])
            try:
                from app.services.ai_service import analyze_bs_pdf
                from app.engine.analyzer import AnalysisResult, MonthlyBreakdown
                from app.engine.validator import validate_analysis
                from app.engine.rule_engine import match_entity, generate_offer_code
                async with aiofiles.open(bs_path, "rb") as fp:
                    bs_bytes = await fp.read()
                ai_bs = await analyze_bs_pdf(bs_bytes, f_info["original_name"] or "statement.pdf")
                if ai_bs:
                    mc = int(ai_bs.get("months_covered", 1)) or 1
                    tc = float(ai_bs.get("total_credits", 0))
                    td = float(ai_bs.get("total_debits", 0))
                    pt = float(ai_bs.get("pos_total", 0))
                    monthly_list = [
                        MonthlyBreakdown(
                            year=m.get("year", 0), month=m.get("month", 0),
                            total_credit=float(m.get("total_credit", 0)),
                            total_debit=float(m.get("total_debit", 0)),
                            pos_credit=float(m.get("pos_credit", 0)),
                            returned_cheques=int(m.get("returned_cheques", 0)),
                        ) for m in ai_bs.get("monthly", [])
                    ]
                    analysis = AnalysisResult(
                        total_credits=tc, total_debits=td, net_revenue=tc - td,
                        avg_monthly_credit=tc / mc, avg_monthly_debit=td / mc,
                        pos_total=pt, pos_percentage=(pt / tc * 100) if tc else 0,
                        returned_cheques_count=int(ai_bs.get("returned_cheques_count", 0)),
                        bounced_percentage=0.0, months_covered=mc,
                        total_transactions=0,
                        max_monthly_drop_pct=float(ai_bs.get("max_monthly_drop_pct", 0)),
                        profit_ratio=float(ai_bs.get("profit_ratio", 0)),
                        confidence_score=float(ai_bs.get("confidence_score", 0.5)),
                        monthly=monthly_list, issues=[], risk_flags=[],
                    )
                    eligible_codes = case.pre_filter_passed or []
                    validation = validate_analysis(
                        analysis,
                        eligible_entity_count=len(eligible_codes),
                        docs_complete=True,
                    )
                    matched_rule, _ = await match_entity(
                        db, analysis, case.age_in_months, case.entity_type,
                        eligible_product_codes=eligible_codes if eligible_codes else None,
                    )
                    case.risk_flags = [
                        {"code": fl.code, "level": fl.level, "title_ar": fl.title_ar,
                         "detail_ar": fl.detail_ar, "value": fl.value, "threshold": fl.threshold}
                        for fl in analysis.risk_flags
                    ]
                    case.risk_flag_count = validation.risk_flag_count
                    case.has_high_risk = validation.has_high_risk
                    case.validation_recommendation = validation.recommendation
                    case.confidence_score = analysis.confidence_score
                    # Merge into analysis_result and clear manual_review flag
                    ar = dict(case.analysis_result or {})
                    ar.pop("pdf_manual_review", None)
                    ar.update({
                        "total_credits": tc, "total_debits": td,
                        "avg_monthly_credit": tc / mc, "net_revenue": tc - td,
                        "pos_total": pt, "months_covered": mc,
                        "bs_source": "supplementary_pdf",
                    })
                    case.analysis_result = ar
                    if not validation.is_valid:
                        case.is_eligible = False
                        case.result_summary = "البيانات المالية تحتاج مراجعة إضافية"
                    elif matched_rule:
                        case.is_eligible = True
                        if not case.offer_code:
                            offer_code = await generate_offer_code(db, matched_rule.offer_code_prefix)
                            case.offer_code = offer_code
                            case.entity_name = matched_rule.entity_name
                        case.result_summary = f"مؤهل — كود العرض: {case.offer_code or ''}"
                        bs_analysis_extra = f"تحليل كشف الحساب: متوسط إيراد شهري {tc / mc:,.0f} ريال، ثقة {analysis.confidence_score:.0%}"
                    else:
                        case.is_eligible = False
                        case.result_summary = "غير مؤهل حالياً بناءً على كشف الحساب"
                        bs_analysis_extra = f"تحليل كشف الحساب: متوسط {tc / mc:,.0f} ريال/شهر"
                else:
                    logger.warning("BS PDF analysis in supplementary docs returned empty")
            except Exception as _bse:
                logger.warning(f"BS PDF supplementary analysis error: {_bse}")
            break  # only process first matching file

    # ── AI: generate Arabic summary of what was uploaded ────────────────────
    ai_summary = ""
    try:
        ai_summary = await summarize_supplementary_docs(
            [d["label"] for d in saved_files],
            company_name=case.company_name or "",
        )
    except Exception as _ae:
        logger.warning(f"Doc AI summary skipped: {_ae}")

    # ── Advance stage: completing_request → fee_contract_signed ───────────
    next_stage_val = case.stage.value if hasattr(case.stage, 'value') else str(case.stage)
    if case.stage == CaseStage.completing_request:
        try:
            idx = STAGES_ORDER.index(CaseStage.completing_request)
            next_s = STAGES_ORDER[idx + 1]
            case.stage = next_s
            case.last_stage_change_at = datetime.utcnow()
            next_stage_val = next_s.value
            db.add(CaseStageHistory(
                case_id=case.id,
                stage=next_s,
                updated_by=current_user.id,
                updated_by_role=current_user.role.value,
                updated_by_name=current_user.name,
                note=f"تم رفع {len(saved_files)} مستند",
            ))
        except (ValueError, IndexError):
            pass

    # Save AI summary into analysis_result
    if ai_summary:
        ar = dict(case.analysis_result or {})
        ar["docs_ai_summary"] = ai_summary
        ar["docs_uploaded_count"] = len(existing_docs)
        case.analysis_result = ar

    db.add(AuditLog(
        case_id=case.id,
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role.value,
        action=AuditAction.file_uploaded,
        details={"action": "documents_uploaded", "count": len(saved_files), "files": uploaded_names},
    ))
    await db.commit()

    combined_summary = " | ".join(filter(None, [bs_analysis_extra, ai_summary]))
    return {
        "message": f"تم رفع {len(saved_files)} مستند بنجاح",
        "files_count": len(saved_files),
        "ai_summary": combined_summary,
        "next_stage": next_stage_val,
        "uploaded_names": uploaded_names,
        "total_docs": len(existing_docs),
        "is_eligible": case.is_eligible,
    }


@router.get("/{case_id}/docs/{stored_name}")
async def download_supplementary_doc(
    case_id: str,
    stored_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a supplementary document uploaded during case completion."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    # Access control: partner can only download own case docs
    if current_user.role == UserRole.partner and str(case.partner_id) != str(current_user.id):
        raise HTTPException(403, "غير مخول")

    # Validate the stored_name is in supplementary_docs to prevent path traversal
    docs = case.supplementary_docs or []
    matched = next((d for d in docs if d.get("stored_name") == stored_name), None)
    if not matched:
        raise HTTPException(404, "الملف غير موجود")

    file_path = os.path.join(UPLOAD_DIR, "docs", case_id, stored_name)
    if not os.path.isfile(file_path):
        raise HTTPException(404, "الملف غير متاح على الخادم")

    original_name = matched.get("original_name", stored_name)
    return FileResponse(
        path=file_path,
        filename=original_name,
        media_type="application/octet-stream",
    )
