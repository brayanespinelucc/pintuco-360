"""Real Chromium smoke screenshots: isolated mock API, no private credentials.

Used by .github/workflows/visual-qa.yml. Screenshots are uploaded as CI
artifacts to inspect before merging the visual redesign into Render.
"""
from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

URL = os.environ.get("VISUAL_QA_URL", "http://127.0.0.1:8501")
SHOTS = Path("visual-qa-screenshots")
SHOTS.mkdir(exist_ok=True)

ROLES = ("cliente", "especialista_tecnico", "logistica", "aplicador", "calidad")


def capture(page, name: str) -> None:
    page.screenshot(path=str(SHOTS / f"{name}.png"), full_page=True,
                    animations="disabled", timeout=30000)


def sign_in(page, role: str) -> None:
    page.goto(URL, wait_until="domcontentloaded", timeout=35000)
    expect(page.locator(".cl-auth-showcase")).to_be_visible(timeout=40000)
    expect(page.get_by_role("tab", name="Iniciar sesión")).to_be_visible()
    page.get_by_label("Correo electrónico", exact=True).fill(f"{role}@qa.local")
    page.get_by_label("Contraseña", exact=True).fill("synthetic-qa-password")
    page.get_by_role("button", name="Ingresar a mi espacio").click()
    expect(page.locator(".cl-workspace-bar")).to_be_visible(timeout=40000)
    expect(page.locator(".cl-hero")).to_be_visible()


def check_no_page_overflow(page, label: str) -> None:
    # The seven-stage stepper intentionally scrolls inside .cl-process-scroll.
    # It must not force horizontal scrolling of the entire application.
    width = page.evaluate("""() => ({
        document: document.documentElement.scrollWidth,
        viewport: window.innerWidth
    })""")
    assert width["document"] <= width["viewport"] + 5, (
        f"{label}: viewport overflow {width}"
    )


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            desktop = browser.new_page(viewport={"width": 1440, "height": 900})
            desktop.goto(URL, wait_until="domcontentloaded")
            expect(desktop.locator(".cl-auth-showcase")).to_be_visible(timeout=40000)
            expect(desktop.locator(".cl-auth-form-title")).to_be_visible()
            capture(desktop, "01-login-desktop")

            desktop.get_by_role("tab", name="Crear cuenta").click()
            expect(desktop.get_by_role("button", name="Crear mi cuenta")).to_be_visible()
            capture(desktop, "02-registro-desktop")

            mobile = browser.new_page(
                viewport={"width": 390, "height": 844}, device_scale_factor=1,
                is_mobile=True, has_touch=True,
            )
            mobile.goto(URL, wait_until="domcontentloaded")
            expect(mobile.locator(".cl-auth-showcase")).to_be_visible(timeout=40000)
            capture(mobile, "03-login-mobile")
            check_no_page_overflow(mobile, "Login móvil")

            for role in ROLES:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                sign_in(page, role)
                capture(page, f"04-role-{role}")

                if role == "cliente":
                    expect(page.get_by_text("Solicitud a seguir")).to_be_visible()
                    assert page.locator(".cl-process-steps").count() > 0
                    page.locator('[data-testid="stSidebar"]').get_by_text(
                        "Proyectos", exact=True,
                    ).click()
                    expect(page.get_by_text("Proyectos creados")).to_be_visible(timeout=20000)
                    expect(page.locator(".cl-record-card")).to_have_count(1)
                    capture(page, "05-proyectos-desktop")

                    page.locator('[data-testid="stSidebar"]').get_by_text(
                        "Solicitudes", exact=True,
                    ).click()
                    expect(page.get_by_text("Solicitudes registradas", exact=True)).to_be_visible(
                        timeout=20000,
                    )
                    expect(page.locator(".cl-record-card")).to_have_count(1)
                    capture(page, "06-solicitudes-desktop")
                page.close()

            mobile_user = browser.new_page(
                viewport={"width": 390, "height": 844},
                is_mobile=True, has_touch=True,
            )
            sign_in(mobile_user, "cliente")
            capture(mobile_user, "07-client-mobile")
            check_no_page_overflow(mobile_user, "Panel cliente móvil")
            print("BROWSER QA PASSED: login, signup, 5 roles, client entities, mobile")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
