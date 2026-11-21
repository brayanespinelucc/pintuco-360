"""Premium UX regression: presentation transforms without changing contracts."""
from pathlib import Path

from frontend import premium_components


def test_record_gallery_escapes_untrusted_data_and_keeps_real_fields(monkeypatch):
    html = []
    monkeypatch.setattr(premium_components.st, "html", lambda value: html.append(value))
    premium_components.record_gallery(
        [{
            "nombre_proyecto": "<img src=x onerror=alert(1)>",
            "tipo_superficie": "Concreto & hierro",
            "estado": "en_analisis",
            "area_m2": "85.00",
        }],
        title_key="nombre_proyecto",
        subtitle_key="tipo_superficie",
        badge_key="estado",
        heading="Proyectos",
        detail_keys=(("Área", "area_m2"),),
    )
    assert len(html) == 1
    assert "&lt;img src=x onerror=alert(1)&gt;" in html[0]
    assert "<img src=x onerror" not in html[0]
    assert "Concreto &amp; hierro" in html[0]
    assert "en_analisis" in html[0]
    assert "85.00" in html[0]


def test_gallery_limits_visible_records_without_losing_original_table(monkeypatch):
    output = []
    monkeypatch.setattr(premium_components.st, "html", lambda value: output.append(value))
    records = [{"nombre": f"Empresa {i}"} for i in range(20)]
    premium_components.record_gallery(records, title_key="nombre", max_items=9,
                                      heading="Empresas")
    assert output[0].count('class="cl-record-card"') == 9
    assert "20 registros" in output[0]
    assert "Consulta la tabla completa" in output[0]
    assert "Empresa 19" not in output[0]


def test_onboarding_panel_escapes_values(monkeypatch):
    output = []
    monkeypatch.setattr(premium_components.st, "html", lambda value: output.append(value))
    premium_components.step_intro("02", "<script>", "Crear & verificar")
    assert len(output) == 1
    assert "&lt;script&gt;" in output[0]
    assert "Crear &amp; verificar" in output[0]


def test_premium_shell_is_presentation_only():
    root = Path(__file__).resolve().parents[1]
    design = (root / "frontend" / "design.py").read_text()
    components = (root / "frontend" / "premium_components.py").read_text()
    app = (root / "frontend" / "app.py").read_text()
    assert "def premium_welcome" in design
    assert "def workspace_header" in design
    assert "cl-auth-showcase" in design
    assert "cl-record-grid" in design
    assert "premium_welcome()" in app
    assert "workspace_header(profile" in app
    assert "step_intro(" in app
    assert "record_gallery(" in app
    assert "httpx." not in components
    assert "st.session_state" not in components



def test_core_text_tokens_have_wcag_aa_contrast_against_page_and_panels(monkeypatch):
    """Automated contrast floor for the light/dark CSS token pairs (not a full audit)."""
    import re
    from frontend import design

    emitted = []
    monkeypatch.setattr(design.st, "html", lambda html: emitted.append(html))
    design.apply_design_system(False)
    css = emitted[0].split("COLORLINK STUDIO / Premium editorial design language, 2026.", 1)[1]
    light = css.split('[data-testid="stApp"]:has(#cl-theme-dark)', 1)[0]
    dark = css.split('[data-testid="stApp"]:has(#cl-theme-dark)', 1)[1]

    def css_color(source, name):
        match = re.search(rf"{re.escape(name)}\s*:\s*(#[0-9A-Fa-f]{{6}})", source)
        assert match, f"Missing design token: {name}"
        return match.group(1)

    def luminance(hex_color):
        values = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
                  for v in values]
        return sum(v * factor for v, factor in zip(
            linear, (0.2126, 0.7152, 0.0722)
        ))

    def contrast(fg, bg):
        a, b = sorted((luminance(fg), luminance(bg)))
        return (b + 0.05) / (a + 0.05)

    for mode in (light, dark):
        foreground = [css_color(mode, name) for name in (
            "--cl-text", "--cl-muted", "--cl-turquoise"
        )]
        surfaces = [css_color(mode, name) for name in (
            "--cl-bg", "--cl-panel", "--cl-panel-soft"
        )]
        for fg in foreground:
            for bg in surfaces:
                assert contrast(fg, bg) >= 4.5, (
                    f"Insufficient normal-text contrast: {fg} / {bg}"
                )
