"""Application entrypoint: FastAPI app + in-process API Gateway + static frontend.

Layering:
    frontend (static) -> gateway (middleware) -> api/ -> services/ -> database/

Run (listen on all interfaces so phones/laptops on the same Wi-Fi can reach it):

    uvicorn backend.main:app --host 0.0.0.0 --port 8000
"""
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api import auth as auth_api
from backend.api import health as health_api
from backend.api import users as users_api
from backend.database.database import init_db
from backend.middleware.logging import RequestLoggingMiddleware
from backend.middleware.rate_limit import RateLimitMiddleware

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    init_db()
    yield


app = FastAPI(title="Scalable Auth Platform", version="1.0.0", lifespan=lifespan)

# Create tables eagerly too: TestClient without a lifespan context and
# some edge imports never fire startup events; init_db is idempotent.
init_db()

# --- Gateway middleware (order matters: first added runs last) ---
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local demo; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---
app.include_router(health_api.router)
app.include_router(auth_api.router)
app.include_router(users_api.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):  # noqa: ARG001
    # Never leak internals: generic code + message for unexpected faults.
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {"code": "INTERNAL_ERROR", "message": "Something went wrong. Please try again."},
        },
    )


# --- Frontend (static files) ---
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(FRONTEND_DIR / "index.html")

    for _page in ("login.html", "signup.html", "dashboard.html", "profile.html"):
        _path = FRONTEND_DIR / _page

        def _serve(path=_path):  # bind current path
            return FileResponse(path)

        app.get(f"/{_page}", include_in_schema=False)(_serve)
