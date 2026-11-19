"""Functional Streamlit browser flows over an isolated in-memory FastAPI fixture.

Executes the actual login, signup, client creation forms, and evaluator selector.
Every mutation is local to the workflow runner and recorded as sanitized events.
"""
from __future__ import annotations

import json
import os
from time import monotonic, sleep
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

UI = os.getenv("VISUAL_QA_URL", "http://127.0.0.1:8501")
API = os.getenv("VISUAL_QA_MOCK_API", "http://127.0.0.1:8111")


def events():
    with urlopen(API + "/__qa__/events", timeout=5) as response:
        return json.load(response)["events"]


def matching(path):
    return [e for e in events() if e["path"] == path]


def await_event(path, *, minimum, timeout_seconds=20):
    # Form actions run on Streamlit's separate Python server, not in the
    # browser's HTTP network context. Poll the *local mock fixture* until the
    # server-side call completes instead of racing with the WebSocket rerun.
    deadline = monotonic() + timeout_seconds
    while monotonic() < deadline:
        records = matching(path)
        if len(records) >= minimum:
            return records
        sleep(.15)
    raise AssertionError(
        f"No isolated API event for {path}: expected {minimum}, "
        f"observed {len(matching(path))}"
    )


def sidebar(page, label):
    page.locator('[data-testid="stSidebar"]').get_by_text(
        label, exact=True
    ).click()
    expect(page.locator(".cl-workspace-bar")).to_be_visible(timeout=20000)


def login(page, email):
    page.goto(UI, wait_until="domcontentloaded")
    expect(page.get_by_role("tab", name="Iniciar sesión")).to_be_visible(timeout=35000)
    page.get_by_label("Correo electrónico", exact=True).fill(email)
    page.get_by_label("Contraseña", exact=True).fill("never-used-synthetic-password")
    page.get_by_role("button", name="Ingresar a mi espacio").click()
    expect(page.locator(".cl-workspace-bar")).to_be_visible(timeout=35000)


def test_signup(browser):
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(UI, wait_until="domcontentloaded")
    page.get_by_role("tab", name="Crear cuenta").click()
    expect(page.get_by_label("Nombre completo")).to_be_visible()
    page.get_by_label("Nombre completo").fill("Evaluador de QA")
    page.get_by_label("Correo para registro").fill("qa.registro@example.test")
    page.get_by_label("Crear contraseña (mínimo 8 caracteres)").fill("clave-segura-123")
    page.get_by_label("Confirmar contraseña").fill("diferente")
    # Streamlit renders a visually-hidden native checkbox inside a clickable
    # label. Click its visible text instead of the hidden input.
    page.get_by_text(
        "Confirmo que utilizaré mi propia cuenta para acceder.", exact=True
    ).click()
    expect(page.get_by_role(
        "checkbox", name="Confirmo que utilizaré mi propia cuenta para acceder."
    )).to_be_checked()
    count = len(matching("auth/register"))
    page.get_by_role("button", name="Crear mi cuenta").click()
    expect(page.get_by_text("Las contraseñas no coinciden.")).to_be_visible()
    assert len(matching("auth/register")) == count, (
        "La validación de contraseñas no debe llamar a la API"
    )
    page.get_by_label("Confirmar contraseña").fill("clave-segura-123")
    page.get_by_role("button", name="Crear mi cuenta").click()
    expect(page.get_by_text("Solicitud recibida. Verifica tu correo.")).to_be_visible(
        timeout=20000,
    )
    assert len(matching("auth/register")) == count + 1
    record = matching("auth/register")[-1]
    assert record["has_password"]
    assert not record["has_role"]
    assert record["email"] == "qa.registro@example.test"
    page.close()


def test_client_creation(browser):
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    login(page, "cliente@qa.local")
    assert page.get_by_label("Probar funcionalidades como").count() == 0

    sidebar(page, "Mi empresa")
    page.get_by_label("Nombre de la empresa").fill("Empresa QA integrada")
    page.get_by_label("Ciudad").fill("Medellín")
    before = len(matching("capture/clientes"))
    page.get_by_role("button", name="Guardar empresa").click()
    expect(page.get_by_text("Empresa QA integrada")).to_be_visible(timeout=20000)
    assert len(matching("capture/clientes")) == before + 1

    sidebar(page, "Proyectos")
    page.get_by_label("Nombre del proyecto").fill("Proyecto automatizado premium")
    before = len(matching("capture/proyectos"))
    page.get_by_role("button", name="Crear proyecto").click()
    expect(page.get_by_text("Proyecto automatizado premium")).to_be_visible(
        timeout=20000,
    )
    assert len(matching("capture/proyectos")) == before + 1

    sidebar(page, "Solicitudes")
    page.get_by_label("Descripción de la necesidad").fill(
        "Solicitud de pintura exterior para probar el recorrido sin datos reales."
    )
    before = len(matching("capture/solicitudes"))
    page.get_by_role("button", name="Radicar solicitud").click()
    await_event("capture/solicitudes", minimum=before + 1)
    expect(page.locator(".cl-record-card").filter(has_text=(
        "Solicitud de pintura exterior para probar el recorrido sin datos reales."
    ))).to_be_visible(timeout=20000)
    assert matching("capture/solicitudes")[-1]["fields"] == [
        "descripcion_libre", "proyecto_id",
    ]
    page.close()


def test_evaluator(browser):
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    login(page, "evaluador@qa.local")
    selector = page.get_by_role("combobox", name="Probar funcionalidades como")
    expect(selector).to_be_visible(timeout=20000)
    selector.click()
    page.get_by_role("option", name="Logística").click()
    page.get_by_role("button", name="Cambiar al rol seleccionado").click()
    expect(page.locator(".cl-workspace-bar")).to_contain_text(
        "Logística", timeout=25000
    )
    assert matching("auth/evaluator/role")[-1]["role"] == "logistica"
    selector = page.get_by_role("combobox", name="Probar funcionalidades como")
    selector.click()
    page.get_by_role("option", name="Control de calidad").click()
    page.get_by_role("button", name="Cambiar al rol seleccionado").click()
    expect(page.locator(".cl-workspace-bar")).to_contain_text(
        "Control de calidad", timeout=25000
    )
    assert matching("auth/evaluator/role")[-1]["role"] == "calidad"
    page.close()


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True, args=["--no-sandbox"]
        )
        try:
            test_signup(browser)
            print("Functional browser QA: self-service registration and validation OK")
            test_client_creation(browser)
            print("Functional browser QA: company, project and request creation OK")
            test_evaluator(browser)
            print("Functional browser QA: authorized evaluator role switch OK")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
