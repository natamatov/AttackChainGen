"""
Pydantic схемы для User.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from app.db.models import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    role: UserRole = UserRole.INSTRUCTOR


class UserUpdate(BaseModel):
    full_name: str | None = None
    is_active: bool | None = None


class UserPasswordReset(BaseModel):
    new_password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
