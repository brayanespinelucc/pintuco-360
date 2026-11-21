"""Isolated local browser-QA API: no credentials, services, or Supabase access.

Synthetic records exercise the existing Streamlit presentation through HTTP,
without writing to the production database. Never deploy this module.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from uuid import uuid5, NAMESPACE_URL

app = FastAPI(title="COLORLINK visual QA fixture", docs_url=None, redoc_url=None)
# Process-local, synthetic test state. No real accounts, database, or network writes.
app.state.events = []
app.state.created = {"capture/clientes": [], "capture/proyectos": [], "capture/solicitudes": []}
app.state.evaluator_role = "cliente"


@app.get("/__qa__/events", include_in_schema=False)
async def qa_events():
    """Browser assertions inspect sanitized endpoint, action, and role only."""
    return {"events": app.state.events}


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
    if token == "qa-evaluador":
        return app.state.evaluator_role
    return role if role in ROLE_NAMES else "cliente"


@app.api_route("/api/v1/{path:path}", methods=["GET", "POST"])
async def fake_backend(path: str, request: Request):
    if path == "auth/login" and request.method == "POST":
        payload = await request.json()
        candidate = str(payload.get("email", "")).split("@", 1)[0]
        role = candidate if candidate in ROLE_NAMES else "cliente"
        return {"access_token": "qa-evaluador" if candidate == "evaluador"
                else f"qa-{role}"}
    if path == "auth/register" and request.method == "POST":
        payload = await request.json()
        app.state.events.append({
            "path": path, "email": payload.get("email"),
            "full_name": payload.get("full_name"),
            "has_password": bool(payload.get("password")),
            "has_role": "role" in payload,
        })
        return {"message": "Solicitud recibida. Verifica tu correo.", "requires_confirmation": True}
    if path == "auth/evaluator/role" and request.method == "POST":
        if request.headers.get("authorization") != "Bearer qa-evaluador":
            raise HTTPException(403, detail="Sin autorización para evaluar")
        payload = await request.json()
        role = payload.get("role")
        if role not in ROLE_NAMES:
            raise HTTPException(422, detail="Rol inválido")
        app.state.evaluator_role = role
        app.state.events.append({"path": path, "role": role})
        return {"role": role, "enabled": True}
    if path == "auth/me":
        role = role_from_request(request)
        return {
            "id": COMPANY_ID,
            "role": role,
            "full_name": f"Control visual — {ROLE_NAMES[role]}",
            "email": f"{role}@qa.local",
            "can_switch_roles": request.headers.get("authorization") == "Bearer qa-evaluador",
        }
    if path in app.state.created and request.method == "POST":
        payload = await request.json()
        # Deterministic UUID to keep the fixture repeatable across browser runs.
        suffix = len(app.state.created[path]) + 1
        record_id = str(uuid5(NAMESPACE_URL, f"{path}:{suffix}"))
        record = {"id": record_id, **payload,
                  "created_at": "2026-11-19T14:00:00Z"}
        if path == "capture/solicitudes":
            record["estado"] = "radicada"
        app.state.created[path].append(record)
        app.state.events.append({"path": path, "fields": sorted(payload)})
        return record
    if path == "capture/clientes":
        return [{
            "id": COMPANY_ID, "usuario_id": COMPANY_ID,
            "nombre_empresa": "Constructora Aurora",
            "ciudad": "Bogotá",
            "created_at": "2026-11-19T09:00:00Z",
        }] + app.state.created["capture/clientes"]
    if path == "capture/proyectos":
        return [{
            "id": PROJECT_ID, "cliente_id": COMPANY_ID, "usuario_id": COMPANY_ID,
            "nombre_proyecto": "Renovación de fachadas",
            "area_m2": "85.00", "tipo_superficie": "Concreto",
            "condicion": "Humedad y fisuras", "ambiente": "exterior",
            "color_requerido": "Gris", "fecha_requerida": "2026-12-18",
            "created_at": "2026-11-19T09:00:00Z",
        }] + app.state.created["capture/proyectos"]
    if path == "capture/solicitudes":
        return [{
            "id": REQUEST_ID, "proyecto_id": PROJECT_ID, "usuario_id": COMPANY_ID,
            "estado": "pendiente_informacion",
            "descripcion_libre": "Pintura exterior con evaluación de humedad.",
            "created_at": "2026-11-19T10:20:00Z",
            "updated_at": "2026-11-19T11:30:00Z",
        }] + app.state.created["capture/solicitudes"]
    if request.method == "GET":
        return []
    return {"message": "Solo API local de verificación visual; sin escritura"}
