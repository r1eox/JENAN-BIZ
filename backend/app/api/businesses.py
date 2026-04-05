"""
Business Registry API — establishment records.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.models.business import Business
from app.core.rbac import require_permission
from app.core.dependencies import PaginationParams

router = APIRouter(prefix="/businesses", tags=["businesses"])


class BusinessCreate(BaseModel):
    company_name: str = Field(..., min_length=2)
    cr_number: str = ""
    activity: str = ""
    owner_name: str = ""
    phone: str = ""
    city: str = ""
    establishment_year: str = ""
    notes: str = ""


class BusinessUpdate(BaseModel):
    company_name: str | None = None
    cr_number: str | None = None
    activity: str | None = None
    owner_name: str | None = None
    phone: str | None = None
    city: str | None = None
    establishment_year: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class BusinessOut(BaseModel):
    id: uuid.UUID
    company_name: str
    cr_number: str
    activity: str
    owner_name: str
    phone: str
    city: str
    establishment_year: str
    notes: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class BusinessListResponse(BaseModel):
    items: list[BusinessOut]
    total: int
    page: int
    size: int


@router.get("/", response_model=BusinessListResponse)
async def list_businesses(
    pagination: PaginationParams = Depends(),
    current_user=Depends(require_permission("view_business_registry")),
    db: AsyncSession = Depends(get_db),
):
    query = select(Business).where(Business.is_active == True)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    query = query.order_by(Business.created_at.desc()).offset(pagination.offset).limit(pagination.size)
    items = (await db.execute(query)).scalars().all()
    return BusinessListResponse(items=items, total=total, page=pagination.page, size=pagination.size)


@router.post("/", response_model=BusinessOut, status_code=201)
async def create_business(
    body: BusinessCreate,
    current_user=Depends(require_permission("manage_business_registry")),
    db: AsyncSession = Depends(get_db),
):
    biz = Business(**body.model_dump())
    db.add(biz)
    await db.commit()
    await db.refresh(biz)
    return BusinessOut.model_validate(biz)


@router.patch("/{biz_id}", response_model=BusinessOut)
async def update_business(
    biz_id: uuid.UUID,
    body: BusinessUpdate,
    current_user=Depends(require_permission("manage_business_registry")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Business).where(Business.id == biz_id))
    biz = result.scalar_one_or_none()
    if not biz:
        raise HTTPException(404, "المنشأة غير موجودة")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(biz, k, v)
    await db.commit()
    await db.refresh(biz)
    return BusinessOut.model_validate(biz)


@router.delete("/{biz_id}")
async def delete_business(
    biz_id: uuid.UUID,
    current_user=Depends(require_permission("manage_business_registry")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Business).where(Business.id == biz_id))
    biz = result.scalar_one_or_none()
    if not biz:
        raise HTTPException(404, "المنشأة غير موجودة")
    biz.is_active = False
    await db.commit()
    return {"status": "deleted"}
