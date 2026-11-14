"""RF-07: asignación, ejecución y evidencias de campo en ambiente académico."""
import uuid
from typing import Literal
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field, model_validator

from backend.app.api.capture import current_user, supabase_rest, _config, MAX_FILE_BYTES

router = APIRouter(prefix="/campo", tags=["Ejecución en campo"])
ROLES_ASIGNADORES = {"logistica", "administrador"}
ROLES_SEGUIMIENTO = ROLES_ASIGNADORES | {"aplicador", "cliente", "calidad"}
BUCKET = "colorlink-campo"


def requiere_asignador(profile: dict):
    if profile["role"] not in ROLES_ASIGNADORES:
        raise HTTPException(status_code=403, detail="Solo logística asigna trabajos de campo.")


class AsignarAplicador(BaseModel):
    aplicador_id: uuid.UUID
    observaciones: str = Field(min_length=10, max_length=1500)

    @model_validator(mode="after")
    def normalizar(self):
        if len(self.observaciones.strip()) < 10:
            raise ValueError("Incluye una justificación de al menos 10 caracteres.")
        return self


class EventoCampo(BaseModel):
    tipo: Literal["inicio", "avance", "incidencia", "finalizacion"]
    avance_pct: int | None = Field(default=None, ge=1, le=99)
    observaciones: str = Field(min_length=10, max_length=1500)

    @model_validator(mode="after")
    def validar(self):
        if len(self.observaciones.strip()) < 10:
            raise ValueError("Incluye una observación de al menos 10 caracteres.")
        if self.tipo == "avance" and self.avance_pct is None:
            raise ValueError("Un evento de avance requiere un porcentaje.")
        if self.tipo != "avance" and self.avance_pct is not None:
            raise ValueError("El porcentaje solo se envía en eventos de avance.")
        return self


@router.get("/aplicadores")
async def aplicadores(session=Depends(current_user)):
    profile, token = session
    requiere_asignador(profile)
    result = await supabase_rest("POST", "rpc/campo_aplicadores", token, json={})
    if not isinstance(result, list):
        raise HTTPException(status_code=502, detail="Respuesta de aplicadores inválida.")
    return result


@router.get("/elegibles")
async def elegibles(session=Depends(current_user)):
    profile, token = session
    requiere_asignador(profile)
    result = await supabase_rest("POST", "rpc/campo_elegibles", token, json={})
    if not isinstance(result, list):
        raise HTTPException(status_code=502, detail="Bandeja de campo inválida.")
    return result


@router.get("/aplicaciones")
async def aplicaciones(session=Depends(current_user)):
    profile, token = session
    if profile["role"] not in ROLES_SEGUIMIENTO:
        raise HTTPException(status_code=403, detail="No tienes acceso al seguimiento en campo.")
    result = await supabase_rest("POST", "rpc/campo_listar", token, json={})
    if not isinstance(result, list):
        raise HTTPException(status_code=502, detail="Historial de campo inválido.")
    return result


@router.post("/solicitudes/{solicitud_id}/asignar", status_code=201)
async def asignar(solicitud_id: uuid.UUID, data: AsignarAplicador,
                  session=Depends(current_user)):
    profile, token = session
    requiere_asignador(profile)
    result = await supabase_rest("POST", "rpc/campo_asignar", token, json={
        "p_solicitud_id": str(solicitud_id),
        "p_aplicador_id": str(data.aplicador_id),
        "p_observaciones": data.observaciones.strip(),
    })
    if not isinstance(result, dict) or result.get("solicitud_id") != str(solicitud_id):
        raise HTTPException(status_code=502, detail="No se pudo confirmar la asignación.")
    return result


@router.post("/aplicaciones/{aplicacion_id}/eventos", status_code=201)
async def evento(aplicacion_id: uuid.UUID, data: EventoCampo,
                 session=Depends(current_user)):
    profile, token = session
    if profile["role"] != "aplicador":
        raise HTTPException(status_code=403, detail="Solo el aplicador asignado registra avances.")
    result = await supabase_rest("POST", "rpc/campo_evento", token, json={
        "p_aplicacion_id": str(aplicacion_id),
        "p_tipo": data.tipo,
        "p_avance_pct": data.avance_pct,
        "p_observaciones": data.observaciones.strip(),
    })
    if not isinstance(result, dict) or result.get("estado_aplicacion") is None:
        raise HTTPException(status_code=502, detail="No se pudo confirmar el evento.")
    return result


async def _mis_aplicaciones(profile: dict, token: str):
    if profile["role"] not in ROLES_SEGUIMIENTO:
        raise HTTPException(status_code=403, detail="Acceso no autorizado.")
    records = await supabase_rest("POST", "rpc/campo_listar", token, json={})
    if not isinstance(records, list):
        raise HTTPException(status_code=502, detail="No se pudo consultar el acceso al trabajo.")
    return records


def _buscar_asignacion(records: list, aplicacion_id: uuid.UUID):
    return next((r for r in records if r.get("id") == str(aplicacion_id)), None)


@router.post("/aplicaciones/{aplicacion_id}/evidencias", status_code=201)
async def subir_foto(
    aplicacion_id: uuid.UUID,
    archivo: UploadFile = File(...),
    observaciones: str = Form(...),
    session=Depends(current_user),
):
    profile, token = session
    if profile["role"] != "aplicador":
        raise HTTPException(status_code=403, detail="Solo el aplicador sube fotos de campo.")
    own = _buscar_asignacion(await _mis_aplicaciones(profile, token), aplicacion_id)
    if not own or own["aplicador_id"] != profile["id"]:
        raise HTTPException(status_code=403, detail="El trabajo no está asignado a tu cuenta.")
    if own["estado"] != "en_ejecucion":
        raise HTTPException(status_code=409, detail="Solo se admiten fotografías durante la ejecución.")
    if not (10 <= len(observaciones.strip()) <= 1500):
        raise HTTPException(status_code=422, detail="Las observaciones deben tener de 10 a 1500 caracteres.")
    if not archivo.filename or len(archivo.filename) > 255:
        raise HTTPException(status_code=422, detail="Nombre de archivo inválido.")
    content = await archivo.read(MAX_FILE_BYTES + 1)
    if not content or len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="La fotografía debe tener un tamaño máximo de 5 MB.")
    if content.startswith(b"\xff\xd8\xff") and content.endswith(b"\xff\xd9"):
        mime, extension = "image/jpeg", "jpg"
    elif content.startswith(b"\x89PNG\r\n\x1a\n") and b"IEND" in content[-20:]:
        mime, extension = "image/png", "png"
    else:
        raise HTTPException(status_code=415, detail="Solo se permiten archivos JPEG o PNG válidos.")

    path = f"{profile['id']}/{aplicacion_id}/{uuid.uuid4()}.{extension}"
    root, anon_key = _config()
    storage_url = f"{root}/storage/v1/object/{BUCKET}/{path}"
    headers = {
        "apikey": anon_key, "Authorization": f"Bearer {token}",
        "Content-Type": mime, "x-upsert": "false",
    }
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            result = await client.post(storage_url, headers=headers, content=content)
            if result.status_code not in (200, 201):
                raise HTTPException(status_code=502, detail="No se pudo almacenar la evidencia de campo.")
            try:
                saved = await supabase_rest("POST", "rpc/campo_evidencia", token, json={
                    "p_aplicacion_id": str(aplicacion_id),
                    "p_storage_path": path,
                    "p_mime": mime,
                    "p_bytes": len(content),
                    "p_observaciones": observaciones.strip(),
                })
                if not isinstance(saved, dict) or saved.get("foto_path") != path:
                    raise HTTPException(status_code=502, detail="No se pudo validar la evidencia guardada.")
            except Exception:
                await client.delete(
                    storage_url, headers={"apikey": anon_key, "Authorization": f"Bearer {token}"}
                )
                raise
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Almacenamiento de campo no disponible.") from exc
    return {
        "id": saved["id"], "tipo": saved["tipo"],
        "avance_pct": saved["avance_pct"], "created_at": saved["created_at"],
    }


@router.get("/aplicaciones/{aplicacion_id}/evidencias/{evento_id}/imagen")
async def imagen(aplicacion_id: uuid.UUID, evento_id: uuid.UUID,
                 session=Depends(current_user)):
    profile, token = session
    app = _buscar_asignacion(await _mis_aplicaciones(profile, token), aplicacion_id)
    if not app:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta aplicación.")
    evid = next(
        (e for e in app.get("bitacora", [])
         if e.get("id") == str(evento_id) and e.get("tipo") == "evidencia"),
        None,
    )
    if not evid or not evid.get("foto_path"):
        raise HTTPException(status_code=404, detail="Evidencia no encontrada.")
    root, anon_key = _config()
    storage_url = (
        f"{root}/storage/v1/object/authenticated/{BUCKET}/"
        f"{quote(evid['foto_path'], safe='/')}"
    )
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            result = await client.get(
                storage_url,
                headers={"apikey": anon_key, "Authorization": f"Bearer {token}"},
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="No se pudo leer la evidencia.") from exc
    if result.status_code != 200 or len(result.content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=502, detail="No se pudo recuperar la fotografía privada.")
    mime = evid.get("foto_mime")
    if mime not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=502, detail="Tipo de imagen inválido.")
    return Response(
        result.content, media_type=mime,
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
