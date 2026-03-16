"""
Cases API — CRUD, stage transitions, assignments, notes, approvals.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.case import (
    Case, CaseStage, CaseStageHistory, InternalNote,
    StageApproval, CaseAssignment, ApprovalStatus,
    STAGES_ORDER, GATED_STAGES,
)
from app.models.audit import AuditLog, AuditAction, Notification, NotificationType
from app.schemas.case import (
    CaseResponse, CaseListResponse,
    NoteCreate, NoteResponse,
    ApprovalDecision, ApprovalResponse,
    AssignRequest, AdvanceStageRequest,
    ProposeStageRequest, RejectRequest, KPIResponse,
    OverrideRequest, OverrideResponse, OwnerAnalyticsResponse,
)
from app.core.rbac import (
    get_current_user, require_role,
    can_see_entity_names, can_advance_stage,
    can_approve_transitions, can_reject_case, can_assign_cases,
)
from app.core.dependencies import PaginationParams

router = APIRouter(prefix="/cases", tags=["cases"])


# ─── Helpers ───────────────────────────────────────────

def _case_to_response(
    case: Case,
    user: User,
    partner_name: str = "",
    assigned_to_name: str = "",
) -> CaseResponse:
    """Convert Case model to response, masking entity_name unless owner."""
    resp = CaseResponse.model_validate(case)
    if not can_see_entity_names(user):
        resp.entity_name = None
    resp.partner_name = partner_name
    resp.assigned_to_name = assigned_to_name
    return resp


def _get_next_stage(current: CaseStage) -> CaseStage | None:
    try:
        idx = STAGES_ORDER.index(current)
        if idx + 1 < len(STAGES_ORDER):
            return STAGES_ORDER[idx + 1]
    except ValueError:
        pass
    return None


async def _add_stage_history(
    db: AsyncSession, case: Case, user: User, note: str = ""
):
    entry = CaseStageHistory(
        case_id=case.id,
        stage=case.stage,
        updated_by=user.id,
        updated_by_role=user.role.value,
        updated_by_name=user.name,
        note=note,
    )
    db.add(entry)


async def _log_audit(
    db: AsyncSession, user: User, case: Case, action: AuditAction,
    details: dict | None = None, ip: str = "",
):
    log = AuditLog(
        user_id=user.id,
        user_name=user.name,
        user_role=user.role.value,
        action=action,
        case_id=case.id,
        ip_address=ip,
        details=details,
    )
    db.add(log)


async def _notify(
    db: AsyncSession, user_id: uuid.UUID, ntype: NotificationType,
    title: str, message: str = "", case_id: uuid.UUID | None = None,
):
    notif = Notification(
        user_id=user_id,
        notification_type=ntype,
        title=title,
        message=message,
        case_id=case_id,
    )
    db.add(notif)


# ─── List cases ───────────────────────────────────────

@router.get("/", response_model=CaseListResponse)
async def list_cases(
    stage: str | None = Query(None),
    assigned_to: str | None = Query(None),
    unassigned: bool = Query(False),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List cases based on role and filters."""
    query = select(Case)

    # Partners only see their own cases
    if current_user.role == UserRole.partner:
        query = query.where(Case.partner_id == current_user.id)

    # Filters
    if stage:
        query = query.where(Case.stage == stage)
    if assigned_to:
        query = query.where(Case.assigned_to == uuid.UUID(assigned_to))
    if unassigned:
        query = query.where(Case.assigned_to == None)  # noqa: E711

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate
    query = query.order_by(Case.created_at.desc()).offset(pagination.offset).limit(pagination.size)
    result = await db.execute(query)
    cases = result.scalars().all()

    # Batch-fetch user names
    user_ids = set()
    for c in cases:
        user_ids.add(c.partner_id)
        if c.assigned_to:
            user_ids.add(c.assigned_to)
    users_map: dict[uuid.UUID, str] = {}
    if user_ids:
        ur = await db.execute(select(User).where(User.id.in_(list(user_ids))))
        for u in ur.scalars().all():
            users_map[u.id] = u.name

    return CaseListResponse(
        items=[
            _case_to_response(
                c, current_user,
                partner_name=users_map.get(c.partner_id, ""),
                assigned_to_name=users_map.get(c.assigned_to, "") if c.assigned_to else "",
            )
            for c in cases
        ],
        total=total,
        page=pagination.page,
        size=pagination.size,
    )


# ─── Get single case ─────────────────────────────────

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    # Partners can only see their own
    if current_user.role == UserRole.partner and case.partner_id != current_user.id:
        raise HTTPException(403, "ليس لديك صلاحية لعرض هذا الطلب")

    # Fetch partner name and assigned employee name
    partner_name = ""
    assigned_to_name = ""
    pr = await db.execute(select(User).where(User.id == case.partner_id))
    partner_user = pr.scalar_one_or_none()
    if partner_user:
        partner_name = partner_user.name
    if case.assigned_to:
        ar = await db.execute(select(User).where(User.id == case.assigned_to))
        assigned_user = ar.scalar_one_or_none()
        if assigned_user:
            assigned_to_name = assigned_user.name

    return _case_to_response(case, current_user, partner_name=partner_name, assigned_to_name=assigned_to_name)


# ─── Advance stage ────────────────────────────────────

@router.post("/{case_id}/advance", response_model=CaseResponse)
async def advance_stage(
    case_id: uuid.UUID,
    body: AdvanceStageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not can_advance_stage(current_user):
        raise HTTPException(403, "ليس لديك صلاحية لتقديم المرحلة")

    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    if case.stage == CaseStage.rejected:
        raise HTTPException(400, "لا يمكن تقديم طلب مرفوض")

    next_stage = _get_next_stage(case.stage)
    if not next_stage:
        raise HTTPException(400, "الطلب في المرحلة الأخيرة")

    # Check if gated — employees must propose, not advance directly
    if next_stage in GATED_STAGES and current_user.role == UserRole.employee:
        raise HTTPException(
            400,
            "هذه المرحلة تتطلب موافقة المشرف. استخدم طلب الموافقة بدلاً من ذلك."
        )

    # Advance
    old_stage = case.stage
    case.stage = next_stage
    case.last_stage_change_at = datetime.utcnow()
    case.updated_at = datetime.utcnow()

    await _add_stage_history(db, case, current_user, body.note)
    await _log_audit(db, current_user, case, AuditAction.case_stage_changed, {
        "from": old_stage.value,
        "to": next_stage.value,
    })

    # Notify partner
    await _notify(
        db, case.partner_id, NotificationType.stage_changed,
        f"تم تحديث حالة الطلب إلى: {next_stage.value}",
        case_id=case.id,
    )

    await db.commit()
    await db.refresh(case)
    return _case_to_response(case, current_user)


# ─── Propose stage transition (for gated stages) ─────

@router.post("/{case_id}/propose", response_model=ApprovalResponse)
async def propose_stage(
    case_id: uuid.UUID,
    body: ProposeStageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    target = CaseStage(body.target_stage)
    if target not in GATED_STAGES:
        raise HTTPException(400, "المرحلة المطلوبة لا تتطلب موافقة")

    # Check for existing pending approval
    existing = await db.execute(
        select(StageApproval).where(
            StageApproval.case_id == case_id,
            StageApproval.status == ApprovalStatus.pending,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "يوجد طلب موافقة قيد الانتظار بالفعل")

    approval = StageApproval(
        case_id=case.id,
        stage=target,
        requested_by=current_user.id,
        requested_by_name=current_user.name,
        note=body.note,
    )
    db.add(approval)

    await _log_audit(db, current_user, case, AuditAction.approval_requested, {
        "target_stage": target.value,
    })

    # Notify supervisors
    sup_result = await db.execute(
        select(User).where(User.role.in_([UserRole.supervisor, UserRole.owner]), User.is_active == True)
    )
    for sup in sup_result.scalars().all():
        await _notify(
            db, sup.id, NotificationType.approval_requested,
            f"طلب موافقة: {case.display_id} → {target.value}",
            body.note,
            case.id,
        )

    await db.commit()
    await db.refresh(approval)
    return ApprovalResponse.model_validate(approval)


# ─── Decide approval ──────────────────────────────────

@router.post("/{case_id}/approvals/{approval_id}/decide", response_model=CaseResponse)
async def decide_approval(
    case_id: uuid.UUID,
    approval_id: uuid.UUID,
    body: ApprovalDecision,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not can_approve_transitions(current_user):
        raise HTTPException(403, "ليس لديك صلاحية للموافقة على الانتقالات")

    result = await db.execute(
        select(StageApproval).where(
            StageApproval.id == approval_id,
            StageApproval.case_id == case_id,
        )
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(404, "طلب الموافقة غير موجود")

    if approval.status != ApprovalStatus.pending:
        raise HTTPException(400, "تم البت في هذا الطلب مسبقاً")

    case_result = await db.execute(select(Case).where(Case.id == case_id))
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    approval.approved_by = current_user.id
    approval.approved_by_name = current_user.name
    approval.approved_at = datetime.utcnow()
    approval.note = body.note

    if body.approved:
        approval.status = ApprovalStatus.approved
        old_stage = case.stage
        case.stage = approval.stage
        case.last_stage_change_at = datetime.utcnow()

        await _add_stage_history(db, case, current_user, f"تمت الموافقة: {body.note}")
        await _log_audit(db, current_user, case, AuditAction.approval_granted, {
            "from": old_stage.value, "to": approval.stage.value,
        })
    else:
        approval.status = ApprovalStatus.rejected
        await _log_audit(db, current_user, case, AuditAction.approval_denied, {
            "target_stage": approval.stage.value, "reason": body.note,
        })

    # Notify requester
    await _notify(
        db, approval.requested_by, NotificationType.approval_result,
        f"{'تمت الموافقة' if body.approved else 'تم الرفض'}: {case.display_id}",
        body.note, case.id,
    )

    await db.commit()
    await db.refresh(case)
    return _case_to_response(case, current_user)


# ─── Reject case ──────────────────────────────────────

@router.post("/{case_id}/reject", response_model=CaseResponse)
async def reject_case(
    case_id: uuid.UUID,
    body: RejectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not can_reject_case(current_user):
        raise HTTPException(403, "ليس لديك صلاحية رفض الطلبات")

    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    old_stage = case.stage
    case.stage = CaseStage.rejected
    case.result_summary = f"مرفوض: {body.reason}"
    case.last_stage_change_at = datetime.utcnow()

    await _add_stage_history(db, case, current_user, f"تم الرفض: {body.reason}")
    await _log_audit(db, current_user, case, AuditAction.case_rejected, {
        "from": old_stage.value, "reason": body.reason,
    })
    await _notify(
        db, case.partner_id, NotificationType.case_rejected,
        f"تم رفض الطلب: {case.display_id}", body.reason, case.id,
    )

    await db.commit()
    await db.refresh(case)
    return _case_to_response(case, current_user)


# ─── Cancel case (partner withdraws incomplete wizard) ────────────────────────

@router.post("/{case_id}/cancel", response_model=CaseResponse)
async def cancel_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Allow a partner to cancel their own analyzing case that has no BS uploaded yet."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    # Partners can only cancel their own cases
    if current_user.role == UserRole.partner and case.partner_id != current_user.id:
        raise HTTPException(403, "ليس لديك صلاحية إلغاء هذا الطلب")

    # Non-partners (supervisor/employee/owner) can also cancel analyzing cases
    if current_user.role not in (UserRole.partner, UserRole.supervisor, UserRole.owner):
        raise HTTPException(403, "ليس لديك صلاحية إلغاء الطلبات")

    # Only analyzing cases without a completed BS upload can be cancelled
    if case.stage != CaseStage.analyzing:
        raise HTTPException(400, "لا يمكن إلغاء هذا الطلب في مرحلته الحالية")

    if case.bs_file_name:
        raise HTTPException(400, "لا يمكن إلغاء الطلب بعد رفع كشف الحساب — يرجى التواصل مع الموظف المسؤول")

    old_stage = case.stage
    case.stage = CaseStage.rejected
    case.result_summary = "تم سحب الطلب من قِبَل الشريك"
    case.last_stage_change_at = datetime.utcnow()

    await _add_stage_history(db, case, current_user, "تم سحب الطلب من قِبَل الشريك")
    await _log_audit(db, current_user, case, AuditAction.case_rejected, {
        "from": old_stage.value, "reason": "سحب الشريك",
    })

    await db.commit()
    await db.refresh(case)
    return _case_to_response(case, current_user)


# ─── Assign case ──────────────────────────────────────

@router.post("/{case_id}/assign", response_model=CaseResponse)
async def assign_case(
    case_id: uuid.UUID,
    body: AssignRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not can_assign_cases(current_user):
        raise HTTPException(403, "ليس لديك صلاحية تعيين الطلبات")

    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    # Verify employee exists
    emp_result = await db.execute(select(User).where(User.id == body.employee_id))
    employee = emp_result.scalar_one_or_none()
    if not employee or employee.role != UserRole.employee:
        raise HTTPException(400, "الموظف غير موجود أو ليس بدور موظف")

    case.assigned_to = employee.id

    assignment = CaseAssignment(
        case_id=case.id,
        employee_id=employee.id,
        employee_name=employee.name,
        assigned_by=current_user.id,
    )
    db.add(assignment)

    await _log_audit(db, current_user, case, AuditAction.case_assigned, {
        "employee_id": str(employee.id), "employee_name": employee.name,
    })
    await _notify(
        db, employee.id, NotificationType.case_assigned,
        f"تم تعيين طلب جديد: {case.display_id}", case_id=case.id,
    )

    await db.commit()
    await db.refresh(case)
    return _case_to_response(case, current_user)


# ─── Claim case (employee self-assign) ────────────────

@router.post("/{case_id}/claim", response_model=CaseResponse)
async def claim_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != UserRole.employee:
        raise HTTPException(403, "فقط الموظفون يمكنهم استلام الطلبات")

    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    if case.assigned_to is not None:
        raise HTTPException(400, "الطلب مُعيَّن مسبقاً لموظف آخر")

    case.assigned_to = current_user.id

    assignment = CaseAssignment(
        case_id=case.id,
        employee_id=current_user.id,
        employee_name=current_user.name,
        assigned_by=current_user.id,
    )
    db.add(assignment)

    await _log_audit(db, current_user, case, AuditAction.case_claimed)

    await db.commit()
    await db.refresh(case)
    return _case_to_response(case, current_user)


# ─── Add internal note ───────────────────────────────

@router.post("/{case_id}/notes", response_model=NoteResponse, status_code=201)
async def add_note(
    case_id: uuid.UUID,
    body: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Only staff can add notes
    if current_user.role == UserRole.partner:
        raise HTTPException(403, "الشركاء لا يمكنهم إضافة ملاحظات داخلية")

    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    note = InternalNote(
        case_id=case.id,
        author_id=current_user.id,
        author_name=current_user.name,
        author_role=current_user.role.value,
        note=body.note,
    )
    db.add(note)

    await _log_audit(db, current_user, case, AuditAction.note_added)

    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note)


# ─── Request completion from partner ──────────────────

@router.post("/{case_id}/request-completion", response_model=CaseResponse)
async def request_completion(
    case_id: uuid.UUID,
    body: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == UserRole.partner:
        raise HTTPException(403, "ليس لديك صلاحية")

    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    # Move to completing_request stage
    old_stage = case.stage
    case.stage = CaseStage.completing_request
    case.last_stage_change_at = datetime.utcnow()

    await _add_stage_history(db, case, current_user, f"طلب استكمال: {body.note}")
    await _log_audit(db, current_user, case, AuditAction.completion_requested, {
        "from": old_stage.value, "note": body.note,
    })
    await _notify(
        db, case.partner_id, NotificationType.completion_requested,
        f"مطلوب استكمال بيانات: {case.display_id}", body.note, case.id,
    )

    await db.commit()
    await db.refresh(case)
    return _case_to_response(case, current_user)


# ─── KPIs (supervisor/owner) ──────────────────────────

@router.get("/stats/kpi", response_model=KPIResponse)
async def get_kpis(
    current_user: User = Depends(require_role("supervisor", "owner")),
    db: AsyncSession = Depends(get_db),
):
    from datetime import timedelta

    # Total
    total = (await db.execute(select(func.count()).select_from(Case))).scalar() or 0

    # Completed (fees_received)
    completed = (await db.execute(
        select(func.count()).select_from(Case).where(Case.stage == CaseStage.fees_received)
    )).scalar() or 0

    # Rejected
    rejected = (await db.execute(
        select(func.count()).select_from(Case).where(Case.stage == CaseStage.rejected)
    )).scalar() or 0

    # Pending approval
    pending = (await db.execute(
        select(func.count()).select_from(StageApproval).where(
            StageApproval.status == ApprovalStatus.pending
        )
    )).scalar() or 0

    # Overdue (>48h since last stage change)
    threshold = datetime.utcnow() - timedelta(hours=48)
    overdue = (await db.execute(
        select(func.count()).select_from(Case).where(
            Case.last_stage_change_at < threshold,
            Case.stage != CaseStage.fees_received,
            Case.stage != CaseStage.rejected,
        )
    )).scalar() or 0

    # Stage distribution
    stage_q = await db.execute(
        select(Case.stage, func.count()).group_by(Case.stage)
    )
    stage_dist = {row[0].value: row[1] for row in stage_q.all()}

    # Today new
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_new = (await db.execute(
        select(func.count()).select_from(Case).where(Case.created_at >= today_start)
    )).scalar() or 0

    # Avg transition time (rough: avg hours since last stage change for active cases)
    active_cases = await db.execute(
        select(Case.last_stage_change_at).where(
            Case.stage != CaseStage.fees_received,
            Case.stage != CaseStage.rejected,
        )
    )
    now = datetime.utcnow()
    hours_list = []
    for (lsc,) in active_cases.all():
        if lsc:
            hours_list.append((now - lsc).total_seconds() / 3600)
    avg_hours = sum(hours_list) / len(hours_list) if hours_list else 0

    return KPIResponse(
        total_cases=total,
        completed_cases=completed,
        rejected_cases=rejected,
        pending_approval=pending,
        overdue_cases=overdue,
        avg_transition_hours=round(avg_hours, 1),
        stage_distribution=stage_dist,
        today_new=today_new,
    )


# ─── Owner Override (Manual Decision) ─────────────────

@router.post("/{case_id}/override", response_model=OverrideResponse)
async def override_decision(
    case_id: uuid.UUID,
    body: OverrideRequest,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """Owner-only: override the automated decision on a case."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    if case.stage == CaseStage.fees_received:
        raise HTTPException(400, "لا يمكن تجاوز القرار لطلب مكتمل")

    old_stage = case.stage
    case.is_overridden = True
    case.override_decision = body.decision
    case.override_reason = body.reason
    case.overridden_by = current_user.id
    case.overridden_at = datetime.utcnow()

    if body.decision == "approve":
        case.is_eligible = True
        case.result_summary = f"مؤهل (قرار المالك): {body.reason}"
        if case.stage == CaseStage.analyzing:
            case.stage = CaseStage.completing_request
            case.last_stage_change_at = datetime.utcnow()
    elif body.decision == "reject":
        case.stage = CaseStage.rejected
        case.is_eligible = False
        case.result_summary = f"مرفوض (قرار المالك): {body.reason}"
        case.last_stage_change_at = datetime.utcnow()
    elif body.decision == "refer_review":
        if case.stage in (CaseStage.analyzing, CaseStage.completing_request):
            case.result_summary = f"تمت إحالة الطلب للمراجعة اليدوية: {body.reason}"
        case.stage = CaseStage.completing_request
        case.last_stage_change_at = datetime.utcnow()

    await _add_stage_history(db, case, current_user, f"قرار المالك: {body.decision} — {body.reason}")
    await _log_audit(
        db, current_user, case,
        AuditAction.decision_overridden if body.decision != "refer_review" else AuditAction.referred_to_review,
        {
            "decision": body.decision,
            "reason": body.reason,
            "old_stage": old_stage.value,
            "new_stage": case.stage.value,
        },
    )

    # Notify partner
    await _notify(
        db, case.partner_id, NotificationType.stage_changed,
        f"تم تحديث حالة الطلب: {case.display_id}",
        case.result_summary, case.id,
    )

    await db.commit()

    return OverrideResponse(
        case_id=str(case.id),
        decision=body.decision,
        reason=body.reason,
        overridden_by=current_user.name,
        timestamp=case.overridden_at.isoformat() if case.overridden_at else "",
    )


# ─── Submit to Financing Entity ───────────────────────

class SubmitToEntityBody(BaseModel):
    note: str = ""


@router.post("/{case_id}/submit-to-entity", response_model=CaseResponse)
async def submit_to_entity(
    case_id: uuid.UUID,
    body: SubmitToEntityBody,
    current_user: User = Depends(require_role("supervisor", "owner")),
    db: AsyncSession = Depends(get_db),
):
    """Mark a case as submitted to a financing entity. Supervisor or owner only."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    if case.stage in (CaseStage.analyzing, CaseStage.rejected):
        raise HTTPException(400, "لا يمكن إرسال الطلب في مرحلة التحليل أو الرفض")

    old_stage = case.stage
    case.stage = CaseStage.submitted
    case.last_stage_change_at = datetime.utcnow()

    note_text = f"تم إرسال الطلب للجهة التمويلية{': ' + body.note if body.note else ''}"
    await _add_stage_history(db, case, current_user, note_text)
    await _log_audit(db, current_user, case, AuditAction.stage_advanced, {
        "from": old_stage.value, "to": CaseStage.submitted.value, "note": body.note,
    })

    # Notify partner
    await _notify(
        db, case.partner_id, NotificationType.stage_changed,
        f"طلبك {case.display_id} تم إرساله للجهة التمويلية",
        note_text, case.id,
    )

    await db.commit()
    await db.refresh(case)
    return _case_to_response(case, current_user)


# ─── Owner Analytics (Professional Dashboard) ─────────

@router.get("/stats/owner-analytics", response_model=OwnerAnalyticsResponse)
async def get_owner_analytics(
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """Professional analytics dashboard for the owner."""
    from datetime import timedelta

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Total requests
    total = (await db.execute(select(func.count()).select_from(Case))).scalar() or 0

    # Eligible cases
    eligible = (await db.execute(
        select(func.count()).select_from(Case).where(Case.is_eligible == True)
    )).scalar() or 0

    # Eligibility rate
    eligibility_rate = (eligible / total * 100) if total > 0 else 0

    # Rejected
    rejected = (await db.execute(
        select(func.count()).select_from(Case).where(Case.stage == CaseStage.rejected)
    )).scalar() or 0
    rejection_rate = (rejected / total * 100) if total > 0 else 0

    # Entity distribution (from matched entity names)
    entity_q = await db.execute(
        select(Case.entity_name, func.count())
        .where(Case.entity_name != "", Case.entity_name != None)  # noqa: E711
        .group_by(Case.entity_name)
    )
    entity_distribution = {row[0]: row[1] for row in entity_q.all()}

    # Avg processing time (created_at → fees_received or last_stage_change_at for completed)
    completed_cases_q = await db.execute(
        select(Case.created_at, Case.last_stage_change_at).where(
            Case.stage == CaseStage.fees_received
        )
    )
    hours_list = []
    for created, completed_at in completed_cases_q.all():
        if created and completed_at:
            hours_list.append((completed_at - created).total_seconds() / 3600)
    avg_processing = sum(hours_list) / len(hours_list) if hours_list else 0

    # Total POS volume (from analysis_result JSONB)
    all_cases = await db.execute(
        select(Case.analysis_result).where(Case.analysis_result != None)  # noqa: E711
    )
    total_pos = 0.0
    total_financing = 0.0
    for (ar,) in all_cases.all():
        if ar and isinstance(ar, dict):
            total_pos += ar.get("pos_total", 0) or 0
            total_financing += ar.get("total_credits", 0) or 0

    # This month stats
    completed_this_month = (await db.execute(
        select(func.count()).select_from(Case).where(
            Case.stage == CaseStage.fees_received,
            Case.last_stage_change_at >= month_start,
        )
    )).scalar() or 0

    rejected_this_month = (await db.execute(
        select(func.count()).select_from(Case).where(
            Case.stage == CaseStage.rejected,
            Case.last_stage_change_at >= month_start,
        )
    )).scalar() or 0

    new_this_month = (await db.execute(
        select(func.count()).select_from(Case).where(
            Case.created_at >= month_start,
        )
    )).scalar() or 0

    # Override count
    overridden_count = (await db.execute(
        select(func.count()).select_from(Case).where(Case.is_overridden == True)
    )).scalar() or 0

    # High risk count
    high_risk_count = (await db.execute(
        select(func.count()).select_from(Case).where(Case.has_high_risk == True)
    )).scalar() or 0

    # Auto-approved count
    auto_approved = (await db.execute(
        select(func.count()).select_from(Case).where(
            Case.validation_recommendation == "auto_approve"
        )
    )).scalar() or 0

    # Manual review count
    manual_review = (await db.execute(
        select(func.count()).select_from(Case).where(
            Case.validation_recommendation == "manual_review"
        )
    )).scalar() or 0

    return OwnerAnalyticsResponse(
        total_requests=total,
        eligibility_rate=round(eligibility_rate, 1),
        entity_distribution=entity_distribution,
        rejection_rate=round(rejection_rate, 1),
        avg_processing_hours=round(avg_processing, 1),
        total_pos_volume=round(total_pos, 0),
        expected_total_financing=round(total_financing, 0),
        completed_this_month=completed_this_month,
        rejected_this_month=rejected_this_month,
        new_this_month=new_this_month,
        overridden_count=overridden_count,
        high_risk_count=high_risk_count,
        auto_approved_count=auto_approved,
        manual_review_count=manual_review,
    )


# ─── File Download (with protection) ──────────────────

@router.get("/{case_id}/download/{file_type}")
async def download_file(
    case_id: uuid.UUID,
    file_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Download case files (cr or bs) with access control.
    - Partners can only download their own files.
    - Staff can download files for cases they're assigned to or have access to.
    - No downloads after case reaches fees_received or rejected stage (unless owner).
    """
    import os
    from fastapi.responses import FileResponse

    if file_type not in ("cr", "bs"):
        raise HTTPException(400, "نوع الملف غير صالح. استخدم 'cr' أو 'bs'")

    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "الطلب غير موجود")

    # Partner can only access own files
    if current_user.role == UserRole.partner and case.partner_id != current_user.id:
        await _log_audit(db, current_user, case, AuditAction.file_access_denied, {
            "file_type": file_type, "reason": "unauthorized"
        })
        await db.commit()
        raise HTTPException(403, "ليس لديك صلاحية")

    # Block download after case closure (except owner)
    closed_stages = {CaseStage.fees_received, CaseStage.rejected}
    if case.stage in closed_stages and current_user.role != UserRole.owner:
        await _log_audit(db, current_user, case, AuditAction.file_access_denied, {
            "file_type": file_type, "reason": "case_closed"
        })
        await db.commit()
        raise HTTPException(403, "لا يمكن تحميل الملفات بعد إغلاق الطلب")

    # Determine file path
    file_path = case.cr_file_path if file_type == "cr" else case.bs_file_path
    file_name = case.cr_file_name if file_type == "cr" else case.bs_file_name

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(404, "الملف غير موجود")

    # Audit download
    await _log_audit(db, current_user, case, AuditAction.file_downloaded, {
        "file_type": file_type, "file_name": file_name,
    })
    await db.commit()

    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/octet-stream",
    )


# ─── Notifications ────────────────────────────────────

@router.get("/notifications/list")
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    notifs = result.scalars().all()
    return [
        {
            "id": str(n.id),
            "type": n.notification_type.value,
            "title": n.title,
            "message": n.message,
            "case_id": str(n.case_id) if n.case_id else None,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifs
    ]


@router.post("/notifications/{notif_id}/read")
async def mark_notification_read(
    notif_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notif_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(404, "الإشعار غير موجود")

    notif.is_read = True
    await db.commit()
    return {"status": "ok"}


@router.post("/notifications/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import update
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return {"status": "ok"}
