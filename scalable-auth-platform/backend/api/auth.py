"""Auth API layer (thin: validate HTTP <-> call service layer)."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import User
from backend.models.schemas import LoginRequest, SignupRequest, failure, success
from backend.services import auth_service
from backend.utils import config, security

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "is_active": user.is_active,
    }


@router.post("/signup", status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    try:
        user = auth_service.signup(db, payload.name, payload.email, payload.password)
    except auth_service.AuthError as exc:
        status = 409 if exc.code == "EMAIL_EXISTS" else 400
        return JSONResponse(status_code=status, content=failure(exc.code, exc.message))
    token = security.create_access_token(str(user.id))
    return {"success": True, "data": {"user": _user_payload(user), "access_token": token, "token_type": "bearer"}}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = auth_service.authenticate(db, payload.email, payload.password)
    except auth_service.AuthError as exc:
        return JSONResponse(status_code=401, content=failure(exc.code, exc.message))
    token = security.create_access_token(str(user.id))
    return {"success": True, "data": {"user": _user_payload(user), "access_token": token, "token_type": "bearer"}}


@router.post("/logout")
def logout():
    # JWTs are stateless: the server keeps no session, so "logout" is the
    # client discarding its token. (A denylist/Redis set would be the
    # production upgrade; see docs/scalability.md.)
    return success({"message": "Logged out. Discard the token on the client."})


@router.get("/me")
def me(current: User = Depends(auth_service.get_current_user)):
    return success({"user": _user_payload(current)})


@router.get("/config")
def public_config():
    # Non-sensitive info the frontend may need.
    return success({"token_expire_minutes": config.ACCESS_TOKEN_EXPIRE_MINUTES})
