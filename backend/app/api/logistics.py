"""RF-06: logística académica con reserva FEFO, preparación y despacho auditado."""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from backend.app.api.capture import current_user, supabase_rest

router = APIRouter(prefix="/logistica", tags=["Logística"])
ROLES_OPERADOR = {"logistica", "administrador"}


def exigir_logistica(perfil: dict) -> None:
    if perfil.get("role") not in ROLES_OPERADOR:
        raise HTTPException(status_code=403, detail="Esta operación requiere rol de logística.")


class ObservacionReserva(BaseModel):
    observaciones: str = Field(min_length=10, max_length=1000)

    @model_validator(mode="after")
    def validar(self):
        if len(self.observaciones.strip()) < 10:
            raise ValueError("Las observaciones deben contener al menos 10 caracteres.")
        return self


class AccionLogistica(ObservacionReserva):
    accion: Literal["preparar", "despachar", "cancelar"]


@router.get("/bandeja")
async def bandeja(session=Depends(current_user)):
    profile, token = session
    exigir_logistica(profile)
    resultado = await supabase_rest("POST", "rpc/bandeja_logistica", token, json={})
    if not isinstance(resultado, list):
        raise HTTPException(status_code=502, detail="La bandeja logística devolvió datos inválidos.")
    return resultado


@router.get("/ordenes")
async def ordenes(session=Depends(current_user)):
    profile, token = session
    if profile.get("role") not in ROLES_OPERADOR | {"cliente"}:
        raise HTTPException(status_code=403, detail="Acceso al seguimiento no autorizado.")
    resultado = await supabase_rest(
        "POST", "rpc/listar_ordenes_logisticas", token, json={}
    )
    if not isinstance(resultado, list):
        raise HTTPException(status_code=502, detail="El seguimiento logístico devolvió datos inválidos.")
    return resultado


@router.post("/solicitudes/{solicitud_id}/reservar", status_code=201)
async def reservar(solicitud_id: uuid.UUID, data: ObservacionReserva,
                  session=Depends(current_user)):
    profile, token = session
    exigir_logistica(profile)
    try:
        resultado = await supabase_rest(
            "POST", "rpc/reservar_logistica", token,
            json={
                "p_solicitud_id": str(solicitud_id),
                "p_observaciones": data.observaciones.strip(),
            },
        )
    except HTTPException as exc:
        if exc.status_code == 409:
            raise HTTPException(
                status_code=409,
                detail="No se pudo reservar: revisa aprobación y stock actual. No se reservó parcialmente.",
            ) from exc
        raise
    if not isinstance(resultado, dict) or resultado.get("solicitud_id") != str(solicitud_id):
        raise HTTPException(status_code=502, detail="No se pudo validar la reserva.")
    return resultado


@router.post("/ordenes/{orden_id}/accion", status_code=200)
async def accion(orden_id: uuid.UUID, data: AccionLogistica,
                 session=Depends(current_user)):
    profile, token = session
    exigir_logistica(profile)
    try:
        resultado = await supabase_rest(
            "POST", "rpc/accion_logistica", token,
            json={
                "p_orden_id": str(orden_id),
                "p_accion": data.accion,
                "p_observaciones": data.observaciones.strip(),
            },
        )
    except HTTPException as exc:
        if exc.status_code == 409:
            raise HTTPException(
                status_code=409,
                detail="Transición no permitida: revisa el estado de la orden y de los lotes.",
            ) from exc
        raise
    if not isinstance(resultado, dict) or resultado.get("id") != str(orden_id):
        raise HTTPException(status_code=502, detail="No se pudo confirmar la operación logística.")
    return resultado
