"""RF-02: consulta y procesamiento de una solicitud propia con Gemini."""
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.api.capture import _config, current_user, inserted_one, require_customer, supabase_rest
from backend.app.services.gemini import MAX_PHOTOS, classify_with_gemini

router = APIRouter(prefix="/ia", tags=["Análisis inteligente"])


class ConfirmacionIA(BaseModel):
    autorizo_envio_a_gemini: bool = Field(
        description="El cliente autoriza enviar texto e imágenes a un proveedor externo de IA."
    )


async def _find_request(solicitud_id: uuid.UUID, token: str) -> tuple[dict, dict]:
    requests = await supabase_rest(
        "GET", "solicitudes", token,
        params={"select": "id,proyecto_id,descripcion_libre",
                "id": f"eq.{solicitud_id}", "limit": "1"},
    )
    if not requests:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    request = requests[0]
    projects = await supabase_rest(
        "GET", "proyectos", token,
        params={"select": "id,nombre_proyecto,area_m2,tipo_superficie,condicion,ambiente,color_requerido,fecha_requerida",
                "id": f"eq.{request['proyecto_id']}", "limit": "1"},
    )
    if not projects:
        raise HTTPException(status_code=404, detail="Proyecto asociado no disponible.")
    return request, projects[0]


async def _load_photos(solicitud_id: uuid.UUID, token: str, user_id: str) -> list[tuple[str, bytes]]:
    rows = await supabase_rest(
        "GET", "solicitud_evidencias", token,
        params={"select": "storage_path,mime_type,bytes",
                "solicitud_id": f"eq.{solicitud_id}",
                "order": "created_at.asc", "limit": str(MAX_PHOTOS)},
    )
    if not rows:
        return []
    url, key = _config()
    headers = {"apikey": key, "Authorization": f"Bearer {token}"}
    images = []
    try:
        async with httpx.AsyncClient(timeout=22.0) as client:
            for row in rows:
                path = row["storage_path"]
                if not path.startswith(f"{user_id}/{solicitud_id}/"):
                    raise HTTPException(status_code=403, detail="Fotografía fuera de la solicitud.")
                if row["mime_type"] not in ("image/jpeg", "image/png") or int(row["bytes"]) > 5 * 1024 * 1024:
                    raise HTTPException(status_code=422, detail="Fotografía no compatible con Gemini.")
                response = await client.get(
                    f"{url}/storage/v1/object/authenticated/colorlink-evidencias/{path}",
                    headers=headers,
                )
                if response.is_error:
                    raise HTTPException(status_code=502, detail="No se pudo leer una fotografía privada.")
                content = response.content
                if not content or len(content) > 5 * 1024 * 1024:
                    raise HTTPException(status_code=422, detail="Una fotografía tiene tamaño inválido.")
                images.append((row["mime_type"], content))
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Storage no está disponible.") from exc
    return images


@router.get("/solicitudes/{solicitud_id}/analisis")
async def listar_analisis(solicitud_id: uuid.UUID, session=Depends(current_user)):
    profile, token = session
    require_customer(profile)
    await _find_request(solicitud_id, token)
    return await supabase_rest(
        "GET", "analisis_ia", token,
        params={"select": "id,solicitud_id,modelo,resultado,numero_imagenes,created_at",
                "solicitud_id": f"eq.{solicitud_id}", "order": "created_at.desc", "limit": "10"},
    )


@router.post("/solicitudes/{solicitud_id}/analizar", status_code=201)
async def analizar_solicitud(
    solicitud_id: uuid.UUID, payload: ConfirmacionIA, session=Depends(current_user),
):
    profile, token = session
    require_customer(profile)
    if not payload.autorizo_envio_a_gemini:
        raise HTTPException(status_code=422, detail="Se requiere autorización para enviar datos a Gemini.")

    solicitud, proyecto = await _find_request(solicitud_id, token)
    photos = await _load_photos(solicitud_id, token, profile["id"])
    result, model = await classify_with_gemini(
        description=solicitud["descripcion_libre"], project=proyecto, images=photos,
    )
    record = {
        "solicitud_id": str(solicitud_id),
        "usuario_id": profile["id"],
        "modelo": model,
        "resultado": result.model_dump(mode="json"),
        "numero_imagenes": len(photos),
        "envio_externo_consentido": True,
    }
    return inserted_one(await supabase_rest("POST", "analisis_ia", token, json=record))
