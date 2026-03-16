"""
External Contacts API — Owner manages contacts list for marketing campaigns.
Endpoints:
  GET    /contacts/         → list contacts (paginated, filterable)
  POST   /contacts/         → create contact
  PATCH  /contacts/{id}     → update contact
  DELETE /contacts/{id}     → delete contact
  POST   /contacts/bulk     → import contacts from JSON array
  GET    /contacts/groups   → list distinct group names
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.contact import Contact
from app.core.rbac import require_role
from app.core.dependencies import PaginationParams

router = APIRouter(prefix="/contacts", tags=["contacts"])


# ─── Schemas ────────────────────────────────────────────

class ContactCreate(BaseModel):
    name: str = Field("", max_length=200)
    phone: str = Field(..., min_length=9, max_length=20)
    company_name: str = ""
    group_name: str = "عام"
    notes: str = ""
    tags: list[str] | None = None


class ContactUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    company_name: str | None = None
    group_name: str | None = None
    notes: str | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class ContactOut(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    company_name: str
    group_name: str
    notes: str
    tags: list[str] | None = None
    is_active: bool
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ContactListResponse(BaseModel):
    items: list[ContactOut]
    total: int
    page: int
    size: int


class BulkContactCreate(BaseModel):
    contacts: list[ContactCreate]


class BulkImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


# ─── Endpoints ──────────────────────────────────────────

@router.get("/", response_model=ContactListResponse)
async def list_contacts(
    group: str | None = None,
    search: str | None = None,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    base = select(Contact).where(Contact.is_active == True)

    if group:
        base = base.where(Contact.group_name == group)
    if search:
        base = base.where(
            (Contact.name.ilike(f"%{search}%")) |
            (Contact.phone.ilike(f"%{search}%")) |
            (Contact.company_name.ilike(f"%{search}%"))
        )

    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar() or 0

    q = base.order_by(Contact.created_at.desc()).offset(pagination.offset).limit(pagination.size)
    rows = (await db.execute(q)).scalars().all()

    return ContactListResponse(
        items=[ContactOut.model_validate(c) for c in rows],
        total=total,
        page=pagination.page,
        size=pagination.size,
    )


@router.get("/groups")
async def list_groups(
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """Distinct group names for filtering."""
    result = await db.execute(
        select(distinct(Contact.group_name)).where(Contact.is_active == True)
    )
    groups = [r[0] for r in result.all()]
    return {"groups": groups}


@router.post("/", response_model=ContactOut, status_code=201)
async def create_contact(
    body: ContactCreate,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    # Check duplicate phone
    existing = await db.execute(select(Contact).where(Contact.phone == body.phone))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "رقم الجوال مسجّل مسبقاً في جهات الاتصال")

    contact = Contact(
        name=body.name,
        phone=body.phone,
        company_name=body.company_name,
        group_name=body.group_name,
        notes=body.notes,
        tags=body.tags,
        source="manual",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return ContactOut.model_validate(contact)


@router.patch("/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: uuid.UUID,
    body: ContactUpdate,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(404, "جهة الاتصال غير موجودة")

    if body.name is not None:
        contact.name = body.name
    if body.phone is not None:
        contact.phone = body.phone
    if body.company_name is not None:
        contact.company_name = body.company_name
    if body.group_name is not None:
        contact.group_name = body.group_name
    if body.notes is not None:
        contact.notes = body.notes
    if body.tags is not None:
        contact.tags = body.tags
    if body.is_active is not None:
        contact.is_active = body.is_active

    await db.commit()
    await db.refresh(contact)
    return ContactOut.model_validate(contact)


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(404, "جهة الاتصال غير موجودة")

    await db.delete(contact)
    await db.commit()
    return {"status": "deleted"}


@router.post("/bulk", response_model=BulkImportResult)
async def bulk_import_contacts(
    body: BulkContactCreate,
    current_user: User = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db),
):
    """Import multiple contacts at once. Skips duplicates."""
    imported = 0
    skipped = 0
    errors: list[str] = []

    for item in body.contacts:
        try:
            existing = await db.execute(
                select(Contact).where(Contact.phone == item.phone)
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            contact = Contact(
                name=item.name,
                phone=item.phone,
                company_name=item.company_name,
                group_name=item.group_name,
                notes=item.notes,
                tags=item.tags,
                source="import",
            )
            db.add(contact)
            imported += 1
        except Exception as e:
            errors.append(f"{item.phone}: {str(e)}")

    await db.commit()
    return BulkImportResult(imported=imported, skipped=skipped, errors=errors)
