"""Re-export of the ORM User model for the spec'd `models/user.py` path.

Canonical definition lives in `backend/database/models.py`.
"""
from backend.database.models import User

__all__ = ["User"]
