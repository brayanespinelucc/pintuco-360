from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.auth import router as auth_router
from backend.app.core.config import get_settings

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="API inicial de la plataforma académica Pintuco 360.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["Salud"])
def health() -> dict[str, str]:
    """Comprueba que el proceso API está en funcionamiento, no la salud de Supabase."""
    return {"status": "ok", "service": "pintuco-360-api", "version": "0.1.0"}
