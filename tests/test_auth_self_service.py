"""RF-09: registro público sin elevación de privilegios y roles de evaluador."""
from unittest.mock import AsyncMock

import httpx
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api import auth as auth_api
from backend.app.services import supabase_auth

client = TestClient(app)


def test_registration_accepts_only_identity_not_privileged_role(monkeypatch):
    signup = AsyncMock(return_value={
        "message": "Cuenta registrada. Ya puedes iniciar sesión.",
        "requires_confirmation": False,
    })
    monkeypatch.setattr(auth_api, "signup_with_password", signup)
    res = client.post("/api/v1/auth/register", json={
        "full_name": "Profesor Evaluador",
        "email": "EVALUADOR@EXAMPLE.COM",
        "password": "clavecompleja345",
        "role": "administrador",
        "can_switch_roles": True,
    })
    assert res.status_code == 201, res.text
    assert signup.await_args.args == (
        "evaluador@example.com", "clavecompleja345", "Profesor Evaluador"
    )
    assert res.json()["requires_confirmation"] is False
    assert "access_token" not in res.json()


def test_registration_requires_good_data():
    weak = client.post("/api/v1/auth/register", json={
        "full_name": "A", "email": "not-an-email", "password": "123",
    })
    assert weak.status_code == 422


def test_role_change_requires_authentication_and_allowlisted_role(monkeypatch):
    change = AsyncMock(return_value={"role": "calidad", "enabled": True})
    monkeypatch.setattr(auth_api, "change_evaluator_role", change)
    unauthorized = client.post("/api/v1/auth/evaluator/role", json={"role": "calidad"})
    assert unauthorized.status_code == 401
    assert not change.await_count
    invalid = client.post("/api/v1/auth/evaluator/role",
        headers={"Authorization": "Bearer localtest"},
        json={"role": "administrador"})
    assert invalid.status_code == 422
    assert not change.await_count
    ok = client.post("/api/v1/auth/evaluator/role",
        headers={"Authorization": "Bearer localtest"},
        json={"role": "calidad"})
    assert ok.status_code == 200
    assert change.await_args.args == ("localtest", "calidad")


def test_signup_http_call_does_not_send_any_role(monkeypatch):
    """The database trigger, not request metadata, decides the role."""
    seen = []
    RealClient = httpx.AsyncClient

    def fake_client(*args, **kwargs):
        async def respond(req):
            seen.append(req)
            return httpx.Response(200, json={"user": {"id": "some-user"}})
        return RealClient(transport=httpx.MockTransport(respond))

    monkeypatch.setattr(supabase_auth, "_config", lambda: (
        "https://example.supabase.co", "publishable-value"
    ))
    monkeypatch.setattr(httpx, "AsyncClient", fake_client)
    import asyncio
    result = asyncio.run(supabase_auth.signup_with_password(
        "evaluator@example.com", "password12345", "Evaluador"
    ))
    assert result["requires_confirmation"]
    assert len(seen) == 1
    assert seen[0].url.path == "/auth/v1/signup"
    assert seen[0].url.params["redirect_to"] == "https://colorlink-web-4jb5.onrender.com"
    payload = __import__("json").loads(seen[0].content)
    assert payload == {
        "email": "evaluator@example.com",
        "password": "password12345",
        "data": {"full_name": "Evaluador"},
    }
    assert "role" not in str(payload).lower()


def test_evaluator_role_sql_guards():
    from pathlib import Path
    sql = Path("database/migrations/0012_evaluator_access.sql").read_text()
    assert "p_user_id = auth.uid()" in sql
    assert "e.enabled" in sql
    assert "using errcode='42501'" in sql
    assert "revoke all on private.evaluator_accounts from public,anon,authenticated" in sql
    assert "'administrador'" not in sql.split(
        "create or replace function private.cl_evaluator_change_role", 1
    )[1].split("create or replace function public.evaluator_status", 1)[0]
    assert "private.evaluator_role_events" in sql
    assert "p.role='aplicador'" in sql


def test_resend_confirmation_trusted_redirect_and_minimal_payload(monkeypatch):
    import asyncio
    from backend.app.core.config import Settings
    recorded = []
    RealClient = httpx.AsyncClient

    def fake_client(*args, **kwargs):
        async def respond(req):
            recorded.append(req)
            return httpx.Response(200, json={})
        return RealClient(transport=httpx.MockTransport(respond))

    monkeypatch.setattr(supabase_auth, "_config", lambda: (
        "https://example.supabase.co", "publishable-value"
    ))
    monkeypatch.setattr(supabase_auth, "get_settings", lambda: Settings(
        public_app_url="https://colorlink-web-4jb5.onrender.com"
    ))
    monkeypatch.setattr(httpx, "AsyncClient", fake_client)
    result = asyncio.run(supabase_auth.resend_signup_confirmation("test@example.com"))
    assert "recibirás" in result["message"]
    assert recorded[0].url.path == "/auth/v1/resend"
    assert recorded[0].url.params["redirect_to"] == "https://colorlink-web-4jb5.onrender.com"
    assert __import__("json").loads(recorded[0].content) == {
        "email": "test@example.com", "type": "signup",
    }


def test_resend_confirmation_is_rate_limited_and_never_returns_token(monkeypatch):
    auth_api._resend_last_attempt.clear()
    resend = AsyncMock(return_value={"message": "Si está pendiente recibirás un correo."})
    monkeypatch.setattr(auth_api, "resend_signup_confirmation", resend)
    first = client.post("/api/v1/auth/resend-confirmation", json={"email": "TEST@EXAMPLE.COM"})
    assert first.status_code == 200
    assert "token" not in str(first.json()).lower()
    assert resend.await_args.args == ("test@example.com",)
    second = client.post("/api/v1/auth/resend-confirmation", json={"email": "test@example.com"})
    assert second.status_code == 429
    assert resend.await_count == 1
    auth_api._resend_last_attempt.clear()


def test_explicit_redirect_configuration_rejects_insecure_urls(monkeypatch):
    import pytest
    from fastapi import HTTPException
    from backend.app.core.config import Settings
    for invalid in ["http://localhost:3000", "https://example.com?next=evil",
                    "https://example.com#fragment", "javascript:alert(1)"]:
        monkeypatch.setattr(supabase_auth, "get_settings", lambda: Settings(public_app_url=invalid))
        with pytest.raises(HTTPException):
            supabase_auth._email_redirect_url()
