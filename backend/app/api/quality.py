"""RF-08: inspección humana, checklist, dictámenes y subsanaciones auditadas."""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from backend.app.api.capture import current_user, supabase_rest

router = APIRouter(prefix="/calidad", tags=["Control de calidad"])
ROLES_INSPECTORES = {"calidad", "administrador"}
ROLES_CONSULTA = ROLES_INSPECTORES | {"cliente", "aplicador"}


def requerir_inspector(profile: dict):
    if profile["role"] not in ROLES_INSPECTORES:
        raise HTTPException(
            status_code=403, detail="Solo el inspector de calidad autorizado puede decidir."
        )


class CriteriosCalidad(BaseModel):
    superficie_preparada: bool
    cobertura_adecuada: bool
    acabado_uniforme: bool
    evidencias_verificadas: bool
    incidencias_gestionadas: bool
    model_config = {"extra": "forbid"}


class ResolverCalidad(BaseModel):
    decision: Literal["aprobar", "solicitar_correccion", "rechazar"]
    criterios: CriteriosCalidad
    observaciones: str = Field(min_length=15, max_length=2000)

    @model_validator(mode="after")
    def validar(self):
        if len(self.observaciones.strip()) < 15:
            raise ValueError("La justificación debe tener al menos 15 caracteres.")
        valores = self.criterios.model_dump().values()
        if self.decision == "aprobar" and not all(valores):
            raise ValueError("No se puede aprobar una inspección con criterios incumplidos.")
        if self.decision != "aprobar" and all(valores):
            raise ValueError("Indica al menos un criterio incumplido.")
        return self


@router.get("/bandeja")
async def bandeja(session=Depends(current_user)):
    profile, token = session
    requerir_inspector(profile)
    result = await supabase_rest("POST", "rpc/bandeja_calidad", token, json={})
    if not isinstance(result, list):
        raise HTTPException(status_code=502, detail="La bandeja de calidad devolvió datos inválidos.")
    return result


@router.get("/expedientes")
async def expedientes(session=Depends(current_user)):
    profile, token = session
    if profile["role"] not in ROLES_CONSULTA:
        raise HTTPException(status_code=403, detail="No tienes acceso a expedientes de calidad.")
    result = await supabase_rest("POST", "rpc/expedientes_calidad", token, json={})
    if not isinstance(result, list):
        raise HTTPException(status_code=502, detail="Los expedientes de calidad devolvieron datos inválidos.")
    return result


@router.post("/aplicaciones/{aplicacion_id}/resolver", status_code=201)
async def resolver(
    aplicacion_id: uuid.UUID, payload: ResolverCalidad,
    session=Depends(current_user),
):
    profile, token = session
    requerir_inspector(profile)
    result = await supabase_rest(
        "POST", "rpc/resolver_calidad", token,
        json={
            "p_aplicacion_id": str(aplicacion_id),
            "p_decision": payload.decision,
            "p_criterios": payload.criterios.model_dump(),
            "p_observaciones": payload.observaciones.strip(),
        },
    )
    if (not isinstance(result, dict)
            or result.get("aplicacion_id") != str(aplicacion_id)
            or result.get("decision") != payload.decision):
        raise HTTPException(status_code=502, detail="No se pudo validar el dictamen de calidad.")
    return result
