"""RF-03: consultar catálogo y calcular cantidad para una solicitud propia."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.api.ai import _find_request
from backend.app.api.capture import current_user, inserted_one, require_customer, supabase_rest
from backend.app.services.technical_engine import (
    calcular_materiales, motivos_revision, validar_compatibilidad,
)

router = APIRouter(prefix="/tecnico", tags=["Motor técnico"])


class CalculoRequest(BaseModel):
    producto_id: uuid.UUID


@router.get("/catalogo")
async def listar_catalogo(session=Depends(current_user)):
    profile, token = session
    require_customer(profile)
    return await supabase_rest(
        "GET", "catalogo_productos_tecnicos", token,
        params={
            "select": "id,nombre,fabricante,descripcion,superficie,ambiente,"
                      "rendimiento_m2_litro_mano,manos_recomendadas,desperdicio_pct,"
                      "presentacion_litros,es_demostrativo,activo,ficha_tecnica_url",
            "activo": "eq.true",
            "order": "nombre.asc",
        },
    )


@router.get("/solicitudes/{solicitud_id}/calculos")
async def listar_calculos(solicitud_id: uuid.UUID, session=Depends(current_user)):
    profile, token = session
    require_customer(profile)
    await _find_request(solicitud_id, token)
    return await supabase_rest(
        "GET", "calculos_materiales", token,
        params={"select": "*", "solicitud_id": f"eq.{solicitud_id}",
                "order": "created_at.desc", "limit": "20"},
    )


@router.post("/solicitudes/{solicitud_id}/calcular", status_code=201)
async def registrar_calculo(
    solicitud_id: uuid.UUID, payload: CalculoRequest, session=Depends(current_user),
):
    profile, token = session
    require_customer(profile)
    solicitud, proyecto = await _find_request(solicitud_id, token)

    productos = await supabase_rest(
        "GET", "catalogo_productos_tecnicos", token,
        params={"select": "*", "id": f"eq.{payload.producto_id}",
                "activo": "eq.true", "limit": "1"},
    )
    if not productos:
        raise HTTPException(status_code=404, detail="Producto no disponible.")
    producto = productos[0]
    validar_compatibilidad(proyecto, producto)

    historico_ia = await supabase_rest(
        "GET", "analisis_ia", token,
        params={"select": "resultado", "solicitud_id": f"eq.{solicitud_id}",
                "order": "created_at.desc", "limit": "1"},
    )
    ia_advierte = bool(
        historico_ia and
        historico_ia[0].get("resultado", {}).get("requiere_revision_humana") is True
    )
    motivos = motivos_revision(
        solicitud["descripcion_libre"], proyecto, ia_advierte,
    )
    valores = calcular_materiales(
        area_m2=proyecto["area_m2"],
        rendimiento_m2_litro_mano=producto["rendimiento_m2_litro_mano"],
        manos=producto["manos_recomendadas"],
        desperdicio_pct=producto["desperdicio_pct"],
        presentacion_litros=producto["presentacion_litros"],
    )
    registro = {
        **valores,
        "usuario_id": profile["id"],
        "solicitud_id": str(solicitud_id),
        "producto_id": producto["id"],
        "requiere_revision_humana": bool(motivos),
        "motivos_revision": motivos,
        "es_demostrativo": producto["es_demostrativo"],
    }
    resultado = inserted_one(await supabase_rest(
        "POST", "calculos_materiales", token, json=registro,
    ))
    return {
        **resultado,
        "producto_nombre": producto["nombre"],
        "formula": "(Área × manos / rendimiento por mano) × (1 + desperdicio / 100)",
        "advertencia": (
            "DATOS ACADÉMICOS, NO oficiales de Pintuco. No utilizar para compras."
            if producto["es_demostrativo"]
            else "Validar siempre vigencia de la ficha técnica y condiciones de aplicación."
        ),
    }
