from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routers import auth, dashboard, feedback, learning, students

settings = get_settings()

if settings.is_prod:
    if settings.app_password == "change-me-before-deployment":
        raise RuntimeError("APP_PASSWORD must be changed in production")
    if settings.session_secret == "dev-only-secret-change-me":
        raise RuntimeError("SESSION_SECRET must be changed in production")

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    https_only=settings.session_https_only,
    same_site="lax",
    max_age=60 * 60 * 12,
)

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(learning.router)
app.include_router(dashboard.router)
app.include_router(feedback.router)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")
