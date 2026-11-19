"""Isolated local browser-QA API: no credentials, services, or Supabase access.

Synthetic records exercise the existing Streamlit presentation through HTTP,
without writing to the production database. Never deploy this module.
"""
from __future__ import annotations

from fastapi import FastAPI, Request

app = FastAPI(title="COLORLINK visual QA fixture", docs_url=None, redoc_url=None)

COMPANY_ID = "72ac7d3c-d6cc-4ed8-b3cb-0968fb2c34aa"
PROJECT_ID = "111b81f6-b447-4552-a844-183a68028ad3"
REQUEST_ID = "7de73eb2-fca5-46ab-8ad9-3399a0592e19"
ROLE_NAMES = {
    "cliente": "Cliente",
    "especialista_tecnico": "Especialista técnico",
    "logistica": "Operador de logística",
    "aplicador": "Aplicador",
    "calidad": "Inspector de calidad",
}


def role_from_request(request: Request) -> str:
    token = request.headers.get("authorization", "").removeprefix("Bearer ")
    role = token.removeprefix("qa-")
    return role if role in ROLE_NAMES else "cliente"


@app.api_route("/api/v1/{path:path}", methods=["GET", "POST"])
async def fake_backend(path: str, request: Request):
    if path == "auth/login" and request.method == "POST":
        payload = await request.json()
        candidate = str(payload.get("email", "")).split("@", 1)[0]
        role = candidate if candidate in ROLE_NAMES else "cliente"
        return {"access_token": f"qa-{role}"}
    if path == "auth/register" and request.method == "POST":
        return {"message": "Solicitud recibida. Verifica tu correo.", "requires_confirmation": True}
    if path == "auth/me":
        role = role_from_request(request)
        return {
            "id": COMPANY_ID,
            "role": role,
            "full_name": f"Control visual — {ROLE_NAMES[role]}",
            "email": f"{role}@qa.local",
            "can_switch_roles": False,
        }
    if path == "capture/clientes":
        return [{
            "id": COMPANY_ID, "usuario_id": COMPANY_ID,
            "nombre_empresa": "Constructora Aurora",
            "ciudad": "Bogotá",
            "created_at": "2026-11-19T09:00:00Z",
        }]
    if path == "capture/proyectos":
        return [{
            "id": PROJECT_ID, "cliente_id": COMPANY_ID, "usuario_id": COMPANY_ID,
            "nombre_proyecto": "Renovación de fachadas",
            "area_m2": "85.00", "tipo_superficie": "Concreto",
            "condicion": "Humedad y fisuras", "ambiente": "exterior",
            "color_requerido": "Gris", "fecha_requerida": "2026-12-18",
            "created_at": "2026-11-19T09:00:00Z",
        }]
    if path == "capture/solicitudes":
        return [{
            "id": REQUEST_ID, "proyecto_id": PROJECT_ID, "usuario_id": COMPANY_ID,
            "estado": "pendiente_informacion",
            "descripcion_libre": "Pintura exterior con evaluación de humedad.",
            "created_at": "2026-11-19T10:20:00Z",
            "updated_at": "2026-11-19T11:30:00Z",
        }]
    if request.method == "GET":
        return []
    return {"message": "Solo API local de verificación visual; sin escritura"}
