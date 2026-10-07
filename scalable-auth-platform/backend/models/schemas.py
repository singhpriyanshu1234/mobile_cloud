"""Pydantic request/response schemas (API contract layer)."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

try:
    import pydantic_extra_types  # noqa: F401
    _has_email_validator = True
except ImportError:
    _has_email_validator = False


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class UpdateProfileRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


def success(data: Any) -> dict:
    return {"success": True, "data": data}


def failure(code: str, message: str) -> dict:
    return {"success": False, "error": {"code": code, "message": message}}
