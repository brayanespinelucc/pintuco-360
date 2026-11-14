"""Endpoints RF-01. Supabase REST aplica las políticas RLS de cada usuario."""
import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, model_validator

from backend.app.core.config import get_settings
from backend.app.services.supabase_auth import get_profile

router = APIRouter(prefix="/capture", tags=["Captura de solicitudes"])
bearer = HTTPBearer(auto_error=False)
MAX_FILE_BYTES = 5 * 1024 * 1024


class ClienteCreate(BaseModel):
    nombre_empresa: str = Field(min_length=2, max_length=160)
    ciudad: str = Field(min_length=2, max_length=100)


class ProyectoCreate(BaseModel):
    cliente_id: uuid.UUID
    nombre_proyecto: str = Field(min_length=3, max_length=180)
    area_m2: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    tipo_superficie: str = Field(min_length=2, max_length=100)
    condicion: str = Field(min_length=2, max_length=300)
    ambiente: str
    color_requerido: str = Field(min_length=2, max_length=100)
    fecha_requerida: date | None = None

    @model_validator(mode="after")
    def validate_project(self):
        if self.ambiente not in {"interior", "exterior"}:
            raise ValueError("El ambiente debe ser interior o exterior.")
        if self.fecha_requerida is not None and self.fecha_requerida < date.today():
            raise ValueError("La fecha requerida no puede estar en el pasado.")
        return self


class SolicitudCreate(BaseModel):
    proyecto_id: uuid.UUID
    descripcion_libre: str = Field(min_length=10, max_length=4000)


def _config():
    s = get_settings()
    if not s.supabase_url or not s.supabase_anon_key:
        raise HTTPException(status_code=503, detail="Supabase no está configurado.")
    return s.supabase_url.rstrip("/"), s.supabase_anon_key


async def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión.")
    profile = await get_profile(credentials.credentials)
    return profile, credentials.credentials


def require_customer(profile):
    if profile["role"] != "cliente":
        raise HTTPException(status_code=403, detail="Esta acción está disponible para clientes.")


async def supabase_rest(method: str, table: str, token: str, *, params=None, json=None):
    url, key = _config()
    headers = {
        "apikey": key, "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.request(
                method, f"{url}/rest/v1/{table}",
                headers=headers, params=params, json=json,
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Servicio de datos no disponible.") from exc
    if response.status_code in (401, 403):
        raise HTTPException(status_code=403, detail="Acceso denegado al recurso.")
    if response.status_code >= 400:
        # No filtrar trazas o consultas SQL del proveedor al navegador.
        try:
            db_code = response.json().get("code")
        except (ValueError, AttributeError):
            db_code = None
        if db_code == "42501":
            raise HTTPException(status_code=403, detail="No tienes permisos para esta operación.")
        if db_code == "23514":
            raise HTTPException(
                status_code=409,
                detail="La operación no cumple las condiciones del flujo o ya fue resuelta.",
            )
        if db_code == "22023":
            raise HTTPException(status_code=422, detail="La información enviada no es válida.")
        raise HTTPException(
            status_code=422 if response.status_code == 409 else 502,
            detail="No se pudo completar la operación en la base de datos.",
        )
    try:
        return response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Respuesta de datos inválida.") from exc


def inserted_one(rows):
    if not isinstance(rows, list) or len(rows) != 1:
        raise HTTPException(status_code=502, detail="No se pudo confirmar el registro.")
    return rows[0]


@router.get("/clientes")
async def listar_clientes(session=Depends(current_user)):
    profile, token = session
    require_customer(profile)
    return await supabase_rest("GET", "clientes", token, params={"select": "*", "order": "created_at.desc"})


@router.post("/clientes", status_code=201)
async def crear_cliente(payload: ClienteCreate, session=Depends(current_user)):
    profile, token = session
    require_customer(profile)
    data = payload.model_dump()
    data["usuario_id"] = profile["id"]
    return inserted_one(await supabase_rest("POST", "clientes", token, json=data))


@router.get("/proyectos")
async def listar_proyectos(session=Depends(current_user)):
    profile, token = session
    require_customer(profile)
    return await supabase_rest("GET", "proyectos", token, params={"select": "*", "order": "created_at.desc"})


@router.post("/proyectos", status_code=201)
async def crear_proyecto(payload: ProyectoCreate, session=Depends(current_user)):
    profile, token = session
    require_customer(profile)
    data = payload.model_dump(mode="json")
    data["usuario_id"] = profile["id"]
    return inserted_one(await supabase_rest("POST", "proyectos", token, json=data))


@router.get("/solicitudes")
async def listar_solicitudes(session=Depends(current_user)):
    profile, token = session
    require_customer(profile)
    return await supabase_rest("GET", "solicitudes", token, params={"select": "*", "order": "created_at.desc"})


@router.post("/solicitudes", status_code=201)
async def crear_solicitud(payload: SolicitudCreate, session=Depends(current_user)):
    profile, token = session
    require_customer(profile)
    data = payload.model_dump(mode="json")
    data["usuario_id"] = profile["id"]
    return inserted_one(await supabase_rest("POST", "solicitudes", token, json=data))


@router.get("/solicitudes/{solicitud_id}/evidencias")
async def listar_evidencias(solicitud_id: uuid.UUID, session=Depends(current_user)):
    profile, token = session
    require_customer(profile)
    return await supabase_rest("GET", "solicitud_evidencias", token, params={
        "select": "id,solicitud_id,archivo_original,mime_type,bytes,created_at",
        "solicitud_id": f"eq.{solicitud_id}",
        "order": "created_at.desc"
    })


@router.post("/solicitudes/{solicitud_id}/evidencias", status_code=201)
async def subir_evidencia(solicitud_id: uuid.UUID,
                         archivo: UploadFile = File(...),
                         session=Depends(current_user)):
    profile, token = session
    require_customer(profile)
    rows = await supabase_rest("GET", "solicitudes", token, params={
        "select": "id", "id": f"eq.{solicitud_id}", "limit": "1"
    })
    if not rows:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    if not archivo.filename or len(archivo.filename) > 255:
        raise HTTPException(status_code=422, detail="Nombre de archivo inválido.")
    content = await archivo.read(MAX_FILE_BYTES + 1)
    if not content or len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="La fotografía debe tener entre 1 byte y 5 MB.")
    jpeg = content.startswith(b"\xff\xd8\xff") and content.endswith(b"\xff\xd9")
    png = content.startswith(b"\x89PNG\r\n\x1a\n") and b"IEND" in content[-20:]
    if jpeg:
        mime, extension = "image/jpeg", "jpg"
    elif png:
        mime, extension = "image/png", "png"
    else:
        raise HTTPException(status_code=415, detail="Solo se permiten imágenes JPG o PNG válidas.")

    path = f"{profile['id']}/{solicitud_id}/{uuid.uuid4()}.{extension}"
    url, key = _config()
    headers = {
        "apikey": key, "Authorization": f"Bearer {token}",
        "Content-Type": mime, "x-upsert": "false",
    }
    storage_url = f"{url}/storage/v1/object/colorlink-evidencias/{path}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            upload = await client.post(storage_url, headers=headers, content=content)
            if upload.status_code not in (200, 201):
                raise HTTPException(status_code=502, detail="No fue posible almacenar la fotografía.")
            try:
                saved = inserted_one(await supabase_rest("POST", "solicitud_evidencias", token, json={
                    "solicitud_id": str(solicitud_id),
                    "usuario_id": profile["id"],
                    "storage_path": path,
                    "archivo_original": archivo.filename,
                    "mime_type": mime,
                    "bytes": len(content),
                }))
            except Exception:
                # Evita archivos huérfanos cuando falle la escritura de metadatos.
                await client.delete(storage_url, headers={"apikey": key, "Authorization": f"Bearer {token}"})
                raise
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="No se pudo conectar con almacenamiento.") from exc
    return {key: saved[key] for key in ("id", "solicitud_id", "archivo_original", "mime_type", "bytes", "created_at")}
