"""Pydantic request/response schemas (API contract layer)."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

try:
    from pydantic import ConfigDict as _ConfigDict  # pydantic v2
    _HAS_CONFIG_DICT = True
except ImportError:  # pydantic v1 (requirements-termux.txt)
    _HAS_CONFIG_DICT = False


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

    # v2 style config; v1 style fallback for requirements-termux.txt.
    if _HAS_CONFIG_DICT:
        model_config = _ConfigDict(from_attributes=True)
    else:
        class Config:  # pydantic v1
            orm_mode = True


def success(data: Any) -> dict:
    return {"success": True, "data": data}


def failure(code: str, message: str) -> dict:
    return {"success": False, "error": {"code": code, "message": message}}
