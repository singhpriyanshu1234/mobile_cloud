"""User API layer (protected profile endpoints)."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import User
from backend.models.schemas import UpdateProfileRequest, failure, success
from backend.services import auth_service
from backend.services import user_service

router = APIRouter(prefix="/api/users", tags=["users"])


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "is_active": user.is_active,
    }


@router.get("/me")
def get_me(current: User = Depends(auth_service.get_current_user)):
    return success({"user": _user_payload(current)})


@router.put("/me")
def update_me(
    payload: UpdateProfileRequest,
    current: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    # Re-attach the token user to this request's session.
    user = db.query(User).filter(User.id == current.id).first()
    if user is None or not user.is_active:
        return JSONResponse(status_code=404, content=failure("NOT_FOUND", "User not found."))
    try:
        updated = user_service.update_profile(db, user, payload.name)
    except auth_service.AuthError as exc:
        return JSONResponse(status_code=400, content=failure(exc.code, exc.message))
    return success({"user": _user_payload(updated)})


@router.delete("/me")
def delete_me(
    current: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current.id).first()
    if user is None:
        return JSONResponse(status_code=404, content=failure("NOT_FOUND", "User not found."))
    user_service.delete_account(db, user)
    return success({"message": "Account deleted."})
