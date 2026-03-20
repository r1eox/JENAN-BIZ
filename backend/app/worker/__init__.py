"""
Redis Worker — arq-based background task processor.

Handles:
  1. Bank statement analysis (parse → analyze → validate → match → update case)
  2. Notification dispatch
  3. SLA checks (periodic)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from arq import create_pool
from arq.connections import RedisSettings, ArqRedis
from loguru import logger
from sqlalchemy import select

from app.config import get_settings
from app.database import async_session
from app.models.case import Case, CaseStage, CaseStageHistory
from app.models.audit import AuditLog, AuditAction, Notification, NotificationType
from app.models.user import User, UserRole
from app.engine import parse_bank_statement
from app.engine.analyzer import analyze_transactions
from app.engine.validator import validate_analysis
from app.engine.rule_engine import match_entity, generate_offer_code, financial_check


settings = get_settings()


# ─── Task: Analyze Bank Statement ──────────────────────

async def process_bank_statement(ctx: dict, case_id: str, file_bytes: bytes, required_months: int = 6):
    """
    Full analysis pipeline:
      1. Parse Excel
      2. Analyze transactions
      3. Validate data quality
      4. Match against entity rules
      5. Update case with results
    """
    logger.info(f"[Worker] Processing bank statement for case {case_id}")

    async with async_session() as db:
        try:
            # Load case
            result = await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
            case = result.scalar_one_or_none()
            if not case:
                logger.error(f"Case {case_id} not found")
                return

            # Update progress
            case.analysis_progress = 10
            await db.commit()

            # ── Step 1: Parse ────────────────────────
            parse_result = parse_bank_statement(file_bytes, required_months)
            case.analysis_progress = 30
            await db.commit()

            if parse_result.confidence < 0.1:
                # Completely unparseable
                case.analysis_progress = 100
                case.stage = CaseStage.analyzing  # Stay in analyzing with error
                case.result_summary = "فشل في تحليل الملف: " + "; ".join(parse_result.issues)
                case.confidence_score = parse_result.confidence
                case.analysis_result = {"issues": parse_result.issues, "is_eligible": False}

                await _log_audit(db, case, AuditAction.analysis_failed, {
                    "reason": "unparseable",
                    "issues": parse_result.issues,
                })
                await db.commit()
                return

            # ── Step 2: Analyze ──────────────────────
            analysis = analyze_transactions(parse_result)
            case.analysis_progress = 60
            await db.commit()

            # ── Step 3: Validate ─────────────────────
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

            if analysis.risk_flags:
                await _log_audit(db, case, AuditAction.risk_flags_generated, {
                    "count": len(analysis.risk_flags),
                    "flags": [f.code for f in analysis.risk_flags],
                })

            await db.commit()

            # ── Step 4: Rule engine matching ─────────
            # Use pre-filtered product codes if available, otherwise fallback
            is_rajhi = False  # TODO: detect from bank statement content

            matched_rule, rejection_reasons = await match_entity(
                db, analysis, case.age_in_months, case.entity_type,
                eligible_product_codes=eligible_codes if eligible_codes else None,
                is_rajhi_bank=is_rajhi,
            )
            case.analysis_progress = 90
            await db.commit()

            # ── Step 5: Determine outcome ────────────
            if not validation.is_valid:
                # Low confidence → need more info (stay in completing_request)
                case.stage = CaseStage.completing_request
                case.is_eligible = False
                case.result_summary = "البيانات تحتاج مراجعة إضافية"
                analysis.is_eligible = False
                analysis.rejection_reasons = validation.issues or []

            elif validation.recommendation == "auto_approve" and matched_rule:
                # Auto-approval — single entity, safety margins met, no risk flags
                offer_code = await generate_offer_code(db, matched_rule.offer_code_prefix)
                case.is_eligible = True
                case.entity_name = matched_rule.entity_name
                case.offer_code = offer_code
                case.stage = CaseStage.completing_request
                case.result_summary = f"مؤهل (موافقة تلقائية) — كود العرض: {offer_code}"
                analysis.is_eligible = True
                analysis.matched_entity = matched_rule.entity_name
                analysis.offer_code = offer_code

            elif matched_rule:
                # Eligible but needs manual review (risk flags or multiple entities)
                offer_code = await generate_offer_code(db, matched_rule.offer_code_prefix)
                case.is_eligible = True
                case.entity_name = matched_rule.entity_name
                case.offer_code = offer_code
                case.stage = CaseStage.completing_request
                case.result_summary = f"مؤهل (بانتظار المراجعة) — كود العرض: {offer_code}"
                analysis.is_eligible = True
                analysis.matched_entity = matched_rule.entity_name
                analysis.offer_code = offer_code

            else:
                # Not eligible — no entity matched (partner never sees which entity rejected)
                case.is_eligible = False
                case.stage = CaseStage.completing_request
                case.result_summary = "غير مؤهل حالياً"
                analysis.is_eligible = False
                analysis.rejection_reasons = ["غير مؤهل حالياً — يرجى مراجعة البيانات"]

            # Store full analysis result — preserve partner-entered fields
            _prev_ar = case.analysis_result or {}
            case.confidence_score = analysis.confidence_score
            analysis_result_new = {
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
                "date_range_start": analysis.date_range_start,
                "date_range_end": analysis.date_range_end,
                "total_transactions": analysis.total_transactions,
                "duplicate_count": analysis.duplicate_count,
                "outlier_count": analysis.outlier_count,
                "internal_transfer_count": analysis.internal_transfer_count,
                "reversal_count": analysis.reversal_count,
                "categories": analysis.categories,
                "confidence_score": analysis.confidence_score,
                "is_eligible": analysis.is_eligible,
                "matched_entity": analysis.matched_entity,
                "offer_code": analysis.offer_code,
                "issues": analysis.issues,
                "rejection_reasons": getattr(analysis, "rejection_reasons", []),
                "required_docs": matched_rule.required_docs if matched_rule and matched_rule.required_docs else [],
                "smart_routing_log": rejection_reasons,  # internal-only log (staff/owner)
                "risk_flags": [
                    {"code": f.code, "level": f.level, "title_ar": f.title_ar, "detail_ar": f.detail_ar}
                    for f in analysis.risk_flags
                ],
                "recommendation": validation.recommendation,
                "max_monthly_drop_pct": analysis.max_monthly_drop_pct,
                "profit_ratio": analysis.profit_ratio,
            }
            # Preserve partner-entered financial data and uploaded basic docs
            for _k in ("total_credit", "total_debit", "pos_sales", "other_income", "basic_docs"):
                if _k in _prev_ar:
                    analysis_result_new[_k] = _prev_ar[_k]
            case.analysis_result = analysis_result_new

            case.analysis_progress = 100
            case.last_stage_change_at = datetime.utcnow()

            # Stage history entry
            history = CaseStageHistory(
                case_id=case.id,
                stage=case.stage,
                updated_by=case.partner_id,
                updated_by_role="system",
                updated_by_name="النظام",
                note=f"اكتمل التحليل — الثقة {analysis.confidence_score:.0%}",
            )
            db.add(history)

            # Audit log
            await _log_audit(db, case, AuditAction.analysis_completed, {
                "is_eligible": analysis.is_eligible,
                "confidence": analysis.confidence_score,
                "entity": analysis.matched_entity,
                "offer_code": analysis.offer_code,
            })

            # Notify partner
            notif = Notification(
                user_id=case.partner_id,
                notification_type=NotificationType.stage_changed,
                title="اكتمل تحليل الطلب",
                message=case.result_summary,
                case_id=case.id,
            )
            db.add(notif)

            await db.commit()
            logger.info(f"[Worker] Case {case_id} analysis complete: eligible={analysis.is_eligible}")

        except Exception as e:
            logger.exception(f"[Worker] Error processing case {case_id}: {e}")
            await db.rollback()

            # Try to update case status
            try:
                result = await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
                case = result.scalar_one_or_none()
                if case:
                    case.analysis_progress = 100
                    case.result_summary = f"خطأ في التحليل: {str(e)[:200]}"
                    case.analysis_result = {"error": str(e)[:500], "is_eligible": False}
                    await db.commit()
            except Exception:
                pass


# ─── Task: SLA Check (runs periodically) ──────────────

async def check_sla_overdue(ctx: dict):
    """Check for overdue cases and notify supervisors."""
    from datetime import timedelta

    logger.info("[Worker] Running SLA overdue check")

    async with async_session() as db:
        threshold = datetime.utcnow() - timedelta(hours=48)

        result = await db.execute(
            select(Case)
            .where(Case.last_stage_change_at < threshold)
            .where(Case.stage != CaseStage.fees_received)
            .where(Case.stage != CaseStage.rejected)
        )
        overdue = result.scalars().all()

        if not overdue:
            return

        # Get supervisors
        sup_result = await db.execute(
            select(User).where(User.role == UserRole.supervisor, User.is_active == True)
        )
        supervisors = sup_result.scalars().all()

        for case in overdue:
            for sup in supervisors:
                notif = Notification(
                    user_id=sup.id,
                    notification_type=NotificationType.general,
                    title=f"طلب متأخر: {case.display_id}",
                    message=f"الطلب في مرحلة {case.stage.value} منذ أكثر من 48 ساعة",
                    case_id=case.id,
                )
                db.add(notif)

        await db.commit()
        logger.info(f"[Worker] Found {len(overdue)} overdue cases, notified {len(supervisors)} supervisors")


# ─── Audit helper ──────────────────────────────────────

async def _log_audit(
    db,
    case: Case,
    action: AuditAction,
    details: dict | None = None,
):
    log = AuditLog(
        user_id=case.partner_id,
        user_name="النظام",
        user_role="system",
        action=action,
        case_id=case.id,
        details=details,
    )
    db.add(log)


# ─── Worker configuration ─────────────────────────────

def get_redis_settings() -> RedisSettings:
    """Parse Redis URL into arq RedisSettings."""
    url = settings.REDIS_URL
    # redis://host:port/db
    parts = url.replace("redis://", "").split("/")
    host_port = parts[0].split(":")
    host = host_port[0] if host_port[0] else "localhost"
    port = int(host_port[1]) if len(host_port) > 1 else 6379
    database = int(parts[1]) if len(parts) > 1 and parts[1] else 0

    return RedisSettings(host=host, port=port, database=database)


class WorkerSettings:
    """arq worker configuration."""
    functions = [process_bank_statement, check_sla_overdue]
    redis_settings = get_redis_settings()
    max_jobs = 5
    job_timeout = 300  # 5 minutes per job
    cron_jobs = [
        # Run SLA check every hour
    ]


async def get_redis_pool() -> ArqRedis:
    """Create a Redis connection pool for enqueuing jobs."""
    return await create_pool(get_redis_settings())
