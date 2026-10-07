"""Application configuration via environment variables.

All settings have safe local defaults so the app runs on Termux
with zero configuration. Override via environment or a `.env` file.
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-to-a-long-random-secret-in-production")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = _get_int("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./auth.db")
RATE_LIMIT_PER_MINUTE: int = _get_int("RATE_LIMIT_PER_MINUTE", 100)
LOGIN_RATE_LIMIT_PER_MINUTE: int = _get_int("LOGIN_RATE_LIMIT_PER_MINUTE", 10)
