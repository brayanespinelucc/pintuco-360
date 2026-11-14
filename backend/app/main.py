from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.auth import router as auth_router
from backend.app.api.capture import router as capture_router
from backend.app.api.ai import router as ai_router
from backend.app.api.technical import router as technical_router
from backend.app.api.inventory import router as inventory_router
from backend.app.api.review import router as review_router
from backend.app.core.config import get_settings

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="API académica COLORLINK / Pintuco 360",
    version="0.6.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(capture_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(technical_router, prefix="/api/v1")
app.include_router(inventory_router, prefix="/api/v1")
app.include_router(review_router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["Salud"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "pintuco-360-api", "version": "0.6.0"}
