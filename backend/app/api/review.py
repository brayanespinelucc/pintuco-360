"""RF-05: revisión humana con roles separados y decisiones auditables en Supabase."""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from backend.app.api.capture import current_user, supabase_rest

router = APIRouter(prefix="/revision", tags=["Revisión técnica"])
ROLES_ASESORES = {"asesor", "especialista_tecnico", "administrador"}


def requerir_asesor(perfil: dict) -> None:
    if perfil["role"] not in ROLES_ASESORES:
        raise HTTPException(
            status_code=403, detail="La revisión corresponde a un asesor técnico autorizado."
        )


class CampoCorregido(BaseModel):
    campo: Literal["area_m2", "tipo_superficie", "condicion", "ambiente", "color_requerido"]
    valor_propuesto: str = Field(min_length=2, max_length=180)


class ResolverRevision(BaseModel):
    decision: Literal["aprobar", "rechazar", "solicitar_informacion", "solicitar_correccion"]
    observaciones: str = Field(min_length=10, max_length=2000)
    correccion_propuesta: CampoCorregido | None = None

    @model_validator(mode="after")
    def validar_coherencia(self):
        if self.decision == "solicitar_correccion" and self.correccion_propuesta is None:
            raise ValueError("Debes especificar qué campo corregir y su valor propuesto.")
        if self.decision != "solicitar_correccion" and self.correccion_propuesta is not None:
            raise ValueError("Solo se puede proponer una corrección con esa decisión.")
        if self.correccion_propuesta is not None:
            c = self.correccion_propuesta
            if c.campo == "ambiente" and c.valor_propuesto not in ("interior", "exterior"):
                raise ValueError("El ambiente debe ser interior o exterior.")
        return self


@router.get("/bandeja")
async def bandeja(session=Depends(current_user)):
    perfil, token = session
    requerir_asesor(perfil)
    result = await supabase_rest("POST", "rpc/bandeja_revision_tecnica", token, json={})
    if not isinstance(result, list):
        raise HTTPException(status_code=502, detail="La bandeja devolvió un formato inválido.")
    return result


@router.get("/solicitudes/{solicitud_id}/detalle")
async def detalle(solicitud_id: uuid.UUID, session=Depends(current_user)):
    perfil, token = session
    if perfil["role"] not in ROLES_ASESORES | {"cliente"}:
        raise HTTPException(status_code=403, detail="Rol no autorizado.")
    result = await supabase_rest(
        "POST", "rpc/detalle_revision_tecnica", token,
        json={"p_solicitud_id": str(solicitud_id)},
    )
    if not isinstance(result, dict) or str(result.get("solicitud", {}).get("id")) != str(solicitud_id):
        raise HTTPException(status_code=502, detail="El detalle devolvió un formato inválido.")
    # La RPC vuelve a comprobar auth.uid() y la propiedad de la solicitud.
    return result


@router.post("/solicitudes/{solicitud_id}/resolver", status_code=201)
async def resolver(solicitud_id: uuid.UUID, payload: ResolverRevision,
                   session=Depends(current_user)):
    perfil, token = session
    requerir_asesor(perfil)
    params = {
        "p_solicitud_id": str(solicitud_id),
        "p_decision": payload.decision,
        "p_observaciones": payload.observaciones.strip(),
        "p_correccion_propuesta": (
            payload.correccion_propuesta.model_dump()
            if payload.correccion_propuesta is not None else {}
        ),
    }
    result = await supabase_rest(
        "POST", "rpc/resolver_revision_tecnica", token, json=params
    )
    if not isinstance(result, dict) or result.get("solicitud_id") != str(solicitud_id):
        raise HTTPException(status_code=502, detail="La revisión devolvió un formato inválido.")
    return result
