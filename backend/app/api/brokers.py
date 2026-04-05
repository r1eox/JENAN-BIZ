"""
Brokers API — intermediary/broker registry.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.models.broker import Broker
from app.core.rbac import require_permission
from app.core.dependencies import PaginationParams

router = APIRouter(prefix="/brokers", tags=["brokers"])


class BrokerCreate(BaseModel):
    name: str = Field(..., min_length=2)
    phone: str = ""
    email: str = ""
    company_name: str = ""
    cr_number: str = ""
    city: str = ""
    notes: str = ""


class BrokerUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    company_name: str | None = None
    cr_number: str | None = None
    city: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class BrokerOut(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    email: str
    company_name: str
    cr_number: str
    city: str
    notes: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class BrokerListResponse(BaseModel):
    items: list[BrokerOut]
    total: int
    page: int
    size: int


@router.get("/", response_model=BrokerListResponse)
async def list_brokers(
    pagination: PaginationParams = Depends(),
    current_user=Depends(require_permission("view_brokers")),
    db: AsyncSession = Depends(get_db),
):
    query = select(Broker).where(Broker.is_active == True)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    query = query.order_by(Broker.created_at.desc()).offset(pagination.offset).limit(pagination.size)
    items = (await db.execute(query)).scalars().all()
    return BrokerListResponse(items=items, total=total, page=pagination.page, size=pagination.size)


@router.post("/", response_model=BrokerOut, status_code=201)
async def create_broker(
    body: BrokerCreate,
    current_user=Depends(require_permission("manage_brokers")),
    db: AsyncSession = Depends(get_db),
):
    broker = Broker(**body.model_dump())
    db.add(broker)
    await db.commit()
    await db.refresh(broker)
    return BrokerOut.model_validate(broker)


@router.patch("/{broker_id}", response_model=BrokerOut)
async def update_broker(
    broker_id: uuid.UUID,
    body: BrokerUpdate,
    current_user=Depends(require_permission("manage_brokers")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Broker).where(Broker.id == broker_id))
    broker = result.scalar_one_or_none()
    if not broker:
        raise HTTPException(404, "الوسيط غير موجود")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(broker, k, v)
    await db.commit()
    await db.refresh(broker)
    return BrokerOut.model_validate(broker)


@router.delete("/{broker_id}")
async def delete_broker(
    broker_id: uuid.UUID,
    current_user=Depends(require_permission("manage_brokers")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Broker).where(Broker.id == broker_id))
    broker = result.scalar_one_or_none()
    if not broker:
        raise HTTPException(404, "الوسيط غير موجود")
    broker.is_active = False
    await db.commit()
    return {"status": "deleted"}
