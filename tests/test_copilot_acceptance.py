"""Matriz de aceptación de diez escenarios representativos del copiloto.

Las respuestas Gemini se simulan: la prueba demuestra contratos y matemáticas,
NO la calidad clínica/técnica ni disponibilidad real del proveedor externo.
"""
import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from backend.app.services import copilot as service


SCENARIOS = [
    pytest.param(
        "Pared de 4 m por 2.5 m, dos manos",
        {"intent": "calculo", "parametros": {"ancho_m": 4, "alto_m": 2.5, "manos": 2}, "faltante": ""},
        2.2, id="01-pared-dos-manos",
    ),
    pytest.param(
        "Habitación 4 x 3 x 2.5 metros sin techo",
        {"intent": "calculo", "parametros": {"largo_m": 4, "ancho_m": 3, "altura_m": 2.5}, "faltante": ""},
        7.7, id="02-habitacion-perimetro",
    ),
    pytest.param(
        "Habitación 4 x 3 x 2.5 metros incluyendo techo",
        {"intent": "calculo", "parametros": {"largo_m": 4, "ancho_m": 3, "altura_m": 2.5, "incluir_techo": True}, "faltante": ""},
        10.34, id="03-habitacion-techo",
    ),
    pytest.param(
        "Hay 30 m², descuenta 5 m² de ventanas",
        {"intent": "calculo", "parametros": {"area_m2": 30, "descuento_m2": 5}, "faltante": ""},
        5.5, id="04-area-descuento",
    ),
    pytest.param(
        "Son 20 m² con rendimiento 8 m²/L/mano, 3 manos y 15 % pérdida",
        {"intent": "calculo", "parametros": {"area_m2": 20, "rendimiento_m2_l_mano": 8, "manos": 3, "desperdicio_pct": 15}, "faltante": ""},
        8.63, id="05-rendimiento-confirmado",
    ),
    pytest.param(
        "Dos paredes de 5 x 2 m",
        {"intent": "calculo", "parametros": {"ancho_m": 5, "alto_m": 2, "paredes": 2}, "faltante": ""},
        4.4, id="06-varias-paredes",
    ),
    pytest.param(
        "Quiero estimar pintura, no conozco las medidas",
        {"intent": "calculo", "parametros": {}, "faltante": "¿Cuáles son las medidas de las paredes?"},
        None, id="07-medidas-incompletas",
    ),
    pytest.param(
        "Descuenta el área de la puerta que todavía no he medido",
        {"intent": "calculo", "parametros": {"area_m2": 15}, "faltante": "¿Cuánto mide la puerta?"},
        None, id="08-puerta-sin-medidas",
    ),
    pytest.param(
        "Voy a pintar una fachada, ¿qué pintura compro?",
        {"intent": "orientacion", "parametros": {}, "faltante": ""},
        None, id="09-orientacion-exterior",
    ),
    pytest.param(
        "¿Con qué color combino un piso gris?",
        {"intent": "orientacion", "parametros": {}, "faltante": ""},
        None, id="10-combinacion-colores",
    ),
]


@pytest.mark.parametrize("message,extraction,expected_litres", SCENARIOS)
def test_copilot_acceptance_matrix(monkeypatch, message, extraction, expected_litres):
    reply = "Para esa superficie, verifica preparación y ficha técnica antes de elegir la pintura."
    calls = [json.dumps(extraction)]
    if extraction["intent"] == "orientacion":
        calls.append(reply)
    generate = AsyncMock(side_effect=calls)
    monkeypatch.setattr(service, "_generate", generate)
    output = asyncio.run(service.answer_copilot(message, []))
    assert output["answer"]
    if expected_litres is not None:
        assert output["calculation"]["litros_estimados"] == expected_litres
        assert str(expected_litres) in output["answer"]
        assert generate.await_count == 1
    elif extraction["intent"] == "orientacion":
        assert output["calculation"] is None
        assert output["answer"] == reply
        assert generate.await_count == 2
    else:
        assert output["calculation"] is None
        assert output["answer"] == extraction["faltante"]
        assert generate.await_count == 1


def test_copilot_turn_by_turn_remembers_prior_measurement(monkeypatch):
    generate = AsyncMock(return_value=json.dumps({
        "intent": "calculo",
        "parametros": {"ancho_m": 4, "alto_m": 2.5, "manos": 2},
        "faltante": "",
    }))
    monkeypatch.setattr(service, "_generate", generate)
    result = asyncio.run(service.answer_copilot(
        "La altura es 2,5 metros y quiero dos manos",
        [
            service.ChatMessage(role="user", content="Mi pared tiene 4 metros de ancho"),
            service.ChatMessage(role="assistant", content="¿Cuál es su altura?"),
        ],
    ))
    assert result["calculation"]["litros_estimados"] == 2.2
    assert generate.await_args.args[0][0].content == "Mi pared tiene 4 metros de ancho"
