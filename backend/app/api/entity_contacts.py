"""
Entity Contacts API — employees/reps at funding entities.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.models.entity_contact import EntityContact
from app.core.rbac import require_permission, get_current_user
from app.core.dependencies import PaginationParams

router = APIRouter(prefix="/entity-contacts", tags=["entity-contacts"])


class EntityContactCreate(BaseModel):
    entity_name: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    position: str = ""
    phone: str = ""
    email: str = ""
    notes: str = ""


class EntityContactUpdate(BaseModel):
    entity_name: str | None = None
    name: str | None = None
    position: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class EntityContactOut(BaseModel):
    id: uuid.UUID
    entity_name: str
    name: str
    position: str
    phone: str
    email: str
    notes: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class EntityContactListResponse(BaseModel):
    items: list[EntityContactOut]
    total: int
    page: int
    size: int


@router.get("/", response_model=EntityContactListResponse)
async def list_entity_contacts(
    entity_name: str | None = None,
    pagination: PaginationParams = Depends(),
    current_user=Depends(require_permission("view_entity_contacts")),
    db: AsyncSession = Depends(get_db),
):
    query = select(EntityContact).where(EntityContact.is_active == True)
    if entity_name:
        query = query.where(EntityContact.entity_name == entity_name)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    query = query.order_by(EntityContact.created_at.desc()).offset(pagination.offset).limit(pagination.size)
    items = (await db.execute(query)).scalars().all()

    return EntityContactListResponse(items=items, total=total, page=pagination.page, size=pagination.size)


@router.post("/", response_model=EntityContactOut, status_code=201)
async def create_entity_contact(
    body: EntityContactCreate,
    current_user=Depends(require_permission("manage_entity_contacts")),
    db: AsyncSession = Depends(get_db),
):
    # auto-generate entity_code from entity_name (slug-like)
    code = body.entity_name.strip().replace(" ", "_").lower()[:30] or "unknown"
    data = body.model_dump()
    contact = EntityContact(entity_code=code, **data)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return EntityContactOut.model_validate(contact)


@router.patch("/{contact_id}", response_model=EntityContactOut)
async def update_entity_contact(
    contact_id: uuid.UUID,
    body: EntityContactUpdate,
    current_user=Depends(require_permission("manage_entity_contacts")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EntityContact).where(EntityContact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(404, "جهة الاتصال غير موجودة")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(contact, k, v)
    await db.commit()
    await db.refresh(contact)
    return EntityContactOut.model_validate(contact)


@router.delete("/{contact_id}")
async def delete_entity_contact(
    contact_id: uuid.UUID,
    current_user=Depends(require_permission("manage_entity_contacts")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EntityContact).where(EntityContact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(404, "جهة الاتصال غير موجودة")
    contact.is_active = False
    await db.commit()
    return {"status": "deleted"}
