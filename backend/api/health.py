"""Health endpoints for uptime checks and load-balancer probes."""
from fastapi import APIRouter
from sqlalchemy import text

from backend.database.database import SessionLocal

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health():
    return {"status": "healthy"}


@router.get("/database")
def health_database():
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
        return {"status": "healthy", "database": "online"}
    except Exception:
        return {"status": "unhealthy", "database": "offline"}
