"""Pydantic schemas — Auth, User."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# ─── Auth ───────────────────────────────────────────────

class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=9, max_length=15, description="رقم الجوال")
    password: str = Field(..., min_length=6, description="كلمة المرور")


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, description="الاسم الكامل")
    phone: str = Field(..., min_length=9, max_length=15, description="رقم الجوال")
    password: str = Field(..., min_length=8, description="كلمة المرور")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class RefreshRequest(BaseModel):
    refresh_token: str


# ─── User ───────────────────────────────────────────────

class UserResponse(BaseModel):
    id: UUID
    name: str
    phone: str
    role: str
    is_active: bool
    created_at: datetime
    extra_permissions: list[str] = []

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    phone: str = Field(..., min_length=9, max_length=15)
    password: str = Field(..., min_length=8)
    role: str = Field("partner", description="partner | employee | supervisor | owner")


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    role: str | None = None
    is_active: bool | None = None


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    size: int
