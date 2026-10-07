"""Auth service: registration, credential checks, current-user resolution."""
import re

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import User
from backend.utils import security

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_bearer = HTTPBearer(auto_error=False)


class AuthError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_signup_input(name: str, email: str, password: str) -> None:
    if not name or not name.strip():
        raise AuthError("NAME_REQUIRED", "Name is required.")
    if not email or not _EMAIL_RE.match(email.strip()):
        raise AuthError("INVALID_EMAIL", "Enter a valid email address.")
    if not password or len(password) < 6:
        raise AuthError("WEAK_PASSWORD", "Password must be at least 6 characters.")


def signup(db: Session, name: str, email: str, password: str) -> User:
    email = _normalize_email(email)
    validate_signup_input(name, email, password)
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise AuthError("EMAIL_EXISTS", "An account with this email already exists.")
    user = User(name=name.strip(), email=email, password_hash=security.hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    email = _normalize_email(email)
    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise AuthError("INVALID_CREDENTIALS", "Invalid email or password.")
    if not security.verify_password(password, user.password_hash):
        raise AuthError("INVALID_CREDENTIALS", "Invalid email or password.")
    return user


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="NOT_AUTHENTICATED")
    user_id = security.decode_access_token(creds.credentials)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOKEN")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOKEN")
    return user
