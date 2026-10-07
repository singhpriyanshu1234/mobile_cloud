"""User service: profile read / update / delete."""
from sqlalchemy.orm import Session

from backend.database.models import User
from backend.services.auth_service import AuthError


def update_profile(db: Session, user: User, name: str) -> User:
    name = (name or "").strip()
    if not name:
        raise AuthError("NAME_REQUIRED", "Name is required.")
    if len(name) > 100:
        raise AuthError("NAME_TOO_LONG", "Name must be under 100 characters.")
    user.name = name
    db.commit()
    db.refresh(user)
    return user


def delete_account(db: Session, user: User) -> None:
    # Hard delete for the demo (is_active flag reserved for future soft-delete).
    db.delete(user)
    db.commit()
