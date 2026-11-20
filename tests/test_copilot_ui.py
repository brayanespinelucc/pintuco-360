"""Prueba de regresión: el copiloto nunca pierde preguntas ni errores tras rerun."""
from contextlib import nullcontext
import importlib.util
from pathlib import Path
import types


def _ui_module():
    # Streamlit se importa sin iniciar servidor. No se ejecuta el diálogo.
    spec = importlib.util.spec_from_file_location(
        "copilot_ui_under_test", Path("frontend/copilot_ui.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_chat_retains_prompt_error_and_retries_once(monkeypatch):
    ui = _ui_module()
    state = {}
    monkeypatch.setattr(ui.st, "session_state", state)
    monkeypatch.setattr(ui.st, "spinner", lambda *args, **kwargs: nullcontext())
    ui.prepare_chat("user-a")
    sent = []

    def fake_api(method, path, *, json, return_errors=False):
        sent.append(json)
        assert return_errors is True
        if len(sent) == 1:
            return {"_copilot_error": "Error (503): El copiloto necesita GEMINI_API_KEY en Render."}
        return {"answer": "Te recomiendo comprobar la ficha técnica de la pintura."}

    ui._send(fake_api, "¿Qué pintura necesito?")
    assert state["cl_copilot_history"] == [
        {"role": "user", "content": "¿Qué pintura necesito?"}
    ]
    assert "GEMINI_API_KEY" in state["cl_copilot_error"]
    assert state["cl_copilot_failed_prompt"] == "¿Qué pintura necesito?"
    ui._send(fake_api, "¿Qué pintura necesito?", retry=True)
    assert len(state["cl_copilot_history"]) == 2
    assert state["cl_copilot_history"][0]["role"] == "user"
    assert state["cl_copilot_history"][1]["role"] == "assistant"
    assert sent[1]["history"] == []
    assert "cl_copilot_error" not in state
    assert "cl_copilot_failed_prompt" not in state


def test_chat_separates_histories_by_user(monkeypatch):
    ui = _ui_module()
    state = {}
    monkeypatch.setattr(ui.st, "session_state", state)
    ui.prepare_chat("user-a")
    state["cl_copilot_history"].append({"role": "user", "content": "privado"})
    state["cl_copilot_error"] = "Error previo"
    state["cl_copilot_failed_prompt"] = "privado"
    ui.prepare_chat("user-b")
    assert state["cl_copilot_history"] == []
    assert state["cl_copilot_owner"] == "user-b"
    assert "cl_copilot_error" not in state
    assert "cl_copilot_failed_prompt" not in state


def test_chat_missing_response_is_not_silent(monkeypatch):
    ui = _ui_module()
    state = {}
    monkeypatch.setattr(ui.st, "session_state", state)
    monkeypatch.setattr(ui.st, "spinner", lambda *args, **kwargs: nullcontext())
    ui.prepare_chat("user-a")
    ui._send(lambda *args, **kwargs: None, "Hola")
    assert state["cl_copilot_history"][0]["content"] == "Hola"
    assert "no devolvió una respuesta válida" in state["cl_copilot_error"]


def test_chat_is_limited_and_respects_history(monkeypatch):
    ui = _ui_module()
    state = {}
    monkeypatch.setattr(ui.st, "session_state", state)
    monkeypatch.setattr(ui.st, "spinner", lambda *args, **kwargs: nullcontext())
    ui.prepare_chat("user-a")
    state["cl_copilot_history"] = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"turno {i}"}
        for i in range(20)
    ]
    stored = []

    def fake_api(method, path, *, json, return_errors):
        stored.append(json)
        return {"answer": "Respuesta real proporcionada por la API."}

    ui._send(fake_api, "Una pregunta nueva")
    assert len(stored[0]["history"]) == 12
    assert stored[0]["history"][-1]["content"] == "turno 19"
    assert state["cl_copilot_history"][-1]["role"] == "assistant"
    assert len(state["cl_copilot_history"]) <= 24
