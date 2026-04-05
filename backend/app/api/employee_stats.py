"""
Employee Statistics API — computed from Case data, grouped by assigned employee.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case as sa_case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.case import Case, CaseStage
from app.models.user import User, UserRole
from app.core.rbac import require_permission

router = APIRouter(prefix="/employee-stats", tags=["employee-stats"])


@router.get("/")
async def get_employee_stats(
    current_user=Depends(require_permission("view_employee_stats")),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns per-employee case counts: total, completed, rejected, in_progress.
    Only employees and supervisors are included (not owners or partners).
    """
    # Aggregate case counts grouped by assigned_to
    completed_stages = [
        CaseStage.fees_received.value,
    ]
    rejected_stage = CaseStage.rejected.value

    q = (
        select(
            Case.assigned_to.label("user_id"),
            func.count(Case.id).label("total"),
            func.sum(
                sa_case((Case.stage == CaseStage.fees_received, 1), else_=0)
            ).label("completed"),
            func.sum(
                sa_case((Case.stage == CaseStage.rejected, 1), else_=0)
            ).label("rejected"),
            func.sum(
                sa_case(
                    (
                        Case.stage.not_in([CaseStage.fees_received, CaseStage.rejected]),
                        1,
                    ),
                    else_=0,
                )
            ).label("in_progress"),
        )
        .where(Case.assigned_to.is_not(None))
        .group_by(Case.assigned_to)
    )
    rows = (await db.execute(q)).all()

    # Get user details for those ids
    user_ids = [r.user_id for r in rows]
    if not user_ids:
        return {"stats": []}

    users_q = select(User).where(
        User.id.in_(user_ids),
        User.role.in_([UserRole.employee, UserRole.supervisor]),
    )
    users = {u.id: u for u in (await db.execute(users_q)).scalars().all()}

    stats = []
    for row in rows:
        user = users.get(row.user_id)
        if not user:
            continue
        stats.append({
            "user_id": str(row.user_id),
            "name": user.name,
            "role": user.role.value,
            "total": row.total or 0,
            "completed": row.completed or 0,
            "rejected": row.rejected or 0,
            "in_progress": row.in_progress or 0,
        })

    # Sort by total descending
    stats.sort(key=lambda x: x["total"], reverse=True)
    return {"stats": stats}
