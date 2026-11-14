"""RF-03. Cálculos de volumen determinísticos; no dependen de Gemini."""
import re
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_HALF_UP

from fastapi import HTTPException

Q = Decimal("0.001")
CONDICIONES_CRITICAS = re.compile(
    r"humedad|fisur|grieta|filtraci[oó]n|desprendimient|estructural", re.I
)


def numero_positivo(value, nombre: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=f"{nombre}: número inválido.") from exc
    if not number.is_finite() or number <= 0:
        raise HTTPException(status_code=422, detail=f"{nombre}: debe ser positivo.")
    return number


def calcular_materiales(
    *, area_m2, rendimiento_m2_litro_mano, manos: int,
    desperdicio_pct, presentacion_litros,
) -> dict:
    """Rendimiento medido en m²/L POR MANO, no total para varias manos."""
    area = numero_positivo(area_m2, "Área")
    rendimiento = numero_positivo(rendimiento_m2_litro_mano, "Rendimiento")
    presentacion = numero_positivo(presentacion_litros, "Presentación")
    if isinstance(manos, bool) or not isinstance(manos, int) or not 1 <= manos <= 6:
        raise HTTPException(status_code=422, detail="Manos fuera de rango (1 a 6).")
    try:
        desperdicio = Decimal(str(desperdicio_pct))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail="Desperdicio inválido.") from exc
    if not desperdicio.is_finite() or not Decimal(0) <= desperdicio <= Decimal(50):
        raise HTTPException(status_code=422, detail="Desperdicio fuera de rango (0-50%).")

    litros_teoricos = area * Decimal(manos) / rendimiento
    litros_requeridos = litros_teoricos * (1 + desperdicio / 100)
    # Redondear únicamente DESPUÉS de determinar cuántos envases corresponden.
    envases = int((litros_requeridos / presentacion).to_integral_value(rounding=ROUND_CEILING))
    litros_comerciales = Decimal(envases) * presentacion
    def mostrar(numero):
        return str(numero.quantize(Q, rounding=ROUND_HALF_UP))
    return {
        "area_m2": str(area),
        "rendimiento_m2_litro_mano": str(rendimiento),
        "manos": manos,
        "desperdicio_pct": str(desperdicio),
        "presentacion_litros": str(presentacion),
        "litros_teoricos": mostrar(litros_teoricos),
        "litros_con_desperdicio": mostrar(litros_requeridos),
        "envases": envases,
        "litros_comerciales": mostrar(litros_comerciales),
    }


def validar_compatibilidad(proyecto: dict, producto: dict) -> None:
    superficie = str(proyecto.get("tipo_superficie", "")).strip().casefold()
    destino = str(producto.get("superficie", "")).strip().casefold()
    ambiente = str(proyecto.get("ambiente", "")).strip().casefold()
    previsto = str(producto.get("ambiente", "")).strip().casefold()
    if destino != "cualquiera" and destino not in superficie:
        raise HTTPException(status_code=422, detail="Producto incompatible con la superficie.")
    if previsto not in (ambiente, "ambos"):
        raise HTTPException(status_code=422, detail="Producto incompatible con el ambiente.")


def motivos_revision(descripcion: str, proyecto: dict, ia_advierte: bool) -> list[str]:
    motivos = []
    if CONDICIONES_CRITICAS.search(descripcion + " " + str(proyecto.get("condicion", ""))):
        motivos.append("Condiciones de superficie que requieren inspección técnica (humedad/fisuras).")
    if ia_advierte:
        motivos.append("Gemini solicitó revisión humana.")
    return motivos
