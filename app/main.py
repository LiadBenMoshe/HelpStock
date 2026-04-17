from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.routers.analyze import router as analyze_router

configure_logging()
settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.include_router(analyze_router)


@app.get("/")
async def serve_index() -> FileResponse:
    return FileResponse(static_dir / "index_v2.html")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
