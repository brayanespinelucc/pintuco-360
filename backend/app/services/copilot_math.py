"""Herramientas aritméticas deterministas del copiloto; la IA solo extrae parámetros."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from pydantic import BaseModel, Field, model_validator

US_GALLON_LITERS = Decimal("3.785411784")


class PaintInputs(BaseModel):
    # Área conocida; o pared rectangular; o habitación (perímetro × altura).
    area_m2: Decimal | None = Field(default=None, gt=0, le=50000)
    ancho_m: Decimal | None = Field(default=None, gt=0, le=500)
    alto_m: Decimal | None = Field(default=None, gt=0, le=100)
    paredes: int = Field(default=1, ge=1, le=100)
    largo_m: Decimal | None = Field(default=None, gt=0, le=500)
    altura_m: Decimal | None = Field(default=None, gt=0, le=100)
    descuento_m2: Decimal = Field(default=Decimal("0"), ge=0, le=50000)
    incluir_techo: bool = False
    manos: int = Field(default=2, ge=1, le=8)
    rendimiento_m2_l_mano: Decimal = Field(default=Decimal("10"), gt=0, le=100)
    desperdicio_pct: Decimal = Field(default=Decimal("10"), ge=0, le=50)

    @model_validator(mode="after")
    def validate_geometry(self):
        room = all(v is not None for v in (self.largo_m, self.ancho_m, self.altura_m))
        wall = self.ancho_m is not None and self.alto_m is not None
        if self.area_m2 is None and not (room or wall):
            raise ValueError("Indica área total, ancho y alto de pared o largo, ancho y altura de habitación.")
        if self.incluir_techo and (self.largo_m is None or self.ancho_m is None):
            raise ValueError("Para añadir un techo se necesitan largo y ancho.")
        return self


def _round(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_paint(data: PaintInputs) -> dict:
    """Use SI; rendimiento en m²/litro/mano; sin redondeos intermedios."""
    if data.area_m2 is not None:
        walls = data.area_m2
        method = "área aportada por el usuario"
    elif data.largo_m is not None and data.ancho_m is not None and data.altura_m is not None:
        walls = Decimal("2") * (data.largo_m + data.ancho_m) * data.altura_m
        method = "perímetro de habitación × altura"
    else:
        walls = data.ancho_m * data.alto_m * data.paredes
        method = "ancho × alto × número de paredes"

    ceiling = data.largo_m * data.ancho_m if data.incluir_techo else Decimal("0")
    gross = walls + ceiling
    if gross > Decimal("50000") or data.descuento_m2 >= gross:
        raise ValueError("El descuento debe ser menor al área bruta y el área no puede superar 50000 m².")
    net = gross - data.descuento_m2
    base = net * data.manos / data.rendimiento_m2_l_mano
    excess = base * data.desperdicio_pct / 100
    total = base + excess
    return {
        "metodo": method,
        "paredes_m2": _round(walls),
        "techo_m2": _round(ceiling),
        "area_bruta_m2": _round(gross),
        "descuento_m2": _round(data.descuento_m2),
        "area_neta_m2": _round(net),
        "manos": data.manos,
        "manos_es_supuesto": "manos" not in data.model_fields_set,
        "rendimiento_m2_l_mano": _round(data.rendimiento_m2_l_mano),
        "rendimiento_es_supuesto": "rendimiento_m2_l_mano" not in data.model_fields_set,
        "consumo_base_litros": _round(base),
        "desperdicio_pct": _round(data.desperdicio_pct),
        "desperdicio_es_supuesto": "desperdicio_pct" not in data.model_fields_set,
        "margen_litros": _round(excess),
        "litros_estimados": _round(total),
        "galones_us_estimados": _round(total / US_GALLON_LITERS),
    }


def explain_calculation(result: dict) -> str:
    """Los números de la explicación provienen únicamente del motor matemático."""
    r = result
    rendimiento = " (supuesto orientativo, no ficha técnica)" if r["rendimiento_es_supuesto"] else " (valor informado; comprobar ficha técnica)"
    manos = " (supuesto orientativo)" if r["manos_es_supuesto"] else " (valor informado)"
    margen = " (supuesto orientativo)" if r["desperdicio_es_supuesto"] else " (valor informado)"
    return (
        "**Estimación de pintura de tu proyecto**\n\n"
        f"- Área bruta: **{r['area_bruta_m2']} m²** "
        f"(paredes {r['paredes_m2']} m²; techo {r['techo_m2']} m²).\n"
        f"- Descuento de puertas/ventanas: **{r['descuento_m2']} m²**. "
        f"Área neta: **{r['area_neta_m2']} m²**.\n"
        f"- Manos: **{r['manos']}**{manos}. Rendimiento: **{r['rendimiento_m2_l_mano']} m²/L por mano**{rendimiento}.\n"
        f"- Consumo base = {r['area_neta_m2']} × {r['manos']} ÷ {r['rendimiento_m2_l_mano']} "
        f"= **{r['consumo_base_litros']} L**.\n"
        f"- Margen de {r['desperdicio_pct']} %{margen}: **{r['margen_litros']} L**.\n\n"
        f"**Cantidad final estimada: {r['litros_estimados']} litros** "
        f"(aprox. {r['galones_us_estimados']} galones estadounidenses).\n\n"
        "El consumo real depende del fabricante, porosidad, sellado, preparación y aplicación. "
        "Compra una presentación comercial suficiente según la ficha técnica y disponibilidad comprobada."
    )
