"""Verify self-contained Render deployment without touching production services."""
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from deploy.serve import PRIVATE_API_PORT, commands, public_port_from_env

ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_bundles_both_servers_and_uses_single_public_port():
    dockerfile = (ROOT / "Dockerfile.render").read_text(encoding="utf-8")
    assert "COPY backend/" in dockerfile
    assert "COPY frontend/" in dockerfile
    assert "COPY deploy/" in dockerfile
    assert "CMD [\"python\", \"-m\", \"deploy.serve\"]" in dockerfile
    assert "EXPOSE 10000" in dockerfile
    assert "COPY .env" not in dockerfile
    assert "service_role" not in dockerfile.lower()


def test_web_server_is_public_and_api_private():
    api, ui = commands(10000)
    assert api[api.index("--host") + 1] == "127.0.0.1"
    assert api[api.index("--port") + 1] == str(PRIVATE_API_PORT)
    assert "--server.address=0.0.0.0" in ui
    assert "--server.port=10000" in ui
    assert "--server.enableXsrfProtection=true" in ui
    assert "--server.enableCORS=true" in ui


def test_render_port_is_dynamic():
    with patch.dict(os.environ, {"PORT": "12345"}):
        assert public_port_from_env() == 12345
    with patch.dict(os.environ, {"PORT": "not-a-port"}):
        with pytest.raises(ValueError):
            public_port_from_env()
    with patch.dict(os.environ, {"PORT": "8000"}):
        with pytest.raises(ValueError):
            public_port_from_env()


def test_blueprint_keeps_keys_out_of_git():
    blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")
    assert "name: colorlink-web" in blueprint
    assert "runtime: docker" in blueprint
    assert "plan: free" in blueprint
    assert "healthCheckPath: /_stcore/health" in blueprint
    assert "branch: feat/base-plataforma-pintuco360" in blueprint
    assert "autoDeployTrigger: checksPass" in blueprint
    for name in ("SUPABASE_ANON_KEY", "GEMINI_API_KEY"):
        assert f"- key: {name}\n        sync: false" in blueprint
    assert "SUPABASE_SERVICE_ROLE" not in blueprint
    ignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    assert ".env" in ignore and ".git" in ignore



def test_startup_reports_missing_auth_names_without_revealing_secret_values(monkeypatch, capsys):
    from deploy import serve

    class StopBeforeStarting(RuntimeError):
        pass

    monkeypatch.setenv("PORT", "10000")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "")
    monkeypatch.setattr(serve.signal, "signal", lambda *args: None)
    monkeypatch.setattr(serve.subprocess, "Popen", lambda *args, **kwargs: (_ for _ in ()).throw(StopBeforeStarting()))
    with pytest.raises(StopBeforeStarting):
        serve.main()
    output = capsys.readouterr().out
    assert "missing SUPABASE_ANON_KEY" in output
    assert "https://example.supabase.co" not in output
