"""RF-04: evaluación de stock por lotes, propuesta FEFO sin reserva real."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.api.ai import _find_request
from backend.app.api.capture import current_user, require_customer, supabase_rest

router = APIRouter(prefix="/inventario", tags=["Disponibilidad e inventario"])


class EvaluarStockRequest(BaseModel):
    calculo_id: uuid.UUID


@router.get("/solicitudes/{solicitud_id}/evaluaciones")
async def listar_evaluaciones(solicitud_id: uuid.UUID, session=Depends(current_user)):
    profile, token = session
    require_customer(profile)
    await _find_request(solicitud_id, token)
    return await supabase_rest(
        "GET", "evaluaciones_disponibilidad", token,
        params={
            "select": "*", "solicitud_id": f"eq.{solicitud_id}",
            "order": "created_at.desc", "limit": "20",
        },
    )


@router.post("/solicitudes/{solicitud_id}/evaluar", status_code=201)
async def evaluar(solicitud_id: uuid.UUID, payload: EvaluarStockRequest,
                  session=Depends(current_user)):
    profile, token = session
    require_customer(profile)
    await _find_request(solicitud_id, token)

    # El navegador envía solo el ID del cálculo; nunca cantidades arbitrarias.
    calculos = await supabase_rest(
        "GET", "calculos_materiales", token,
        params={"select": "id,solicitud_id,envases",
                "id": f"eq.{payload.calculo_id}",
                "solicitud_id": f"eq.{solicitud_id}", "limit": "1"},
    )
    if not calculos:
        raise HTTPException(
            status_code=404,
            detail="Cálculo no encontrado en esta solicitud. Realiza primero RF-03.",
        )

    # La RPC verifica auth.uid() y guarda la propuesta sin modificar stock.
    result = await supabase_rest(
        "POST", "rpc/evaluar_disponibilidad_calculo", token,
        json={"p_calculo_id": str(payload.calculo_id)},
    )
    if not isinstance(result, dict) or result.get("solicitud_id") != str(solicitud_id):
        raise HTTPException(status_code=502, detail="No se pudo validar la evaluación de stock.")
    return result
