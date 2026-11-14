import httpx
from fastapi import HTTPException, status

from backend.app.core.config import get_settings


def _config() -> tuple[str, str]:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La autenticación no está configurada en el servidor.",
        )
    return settings.supabase_url.rstrip("/"), settings.supabase_anon_key


async def login_with_password(email: str, password: str) -> dict:
    url, key = _config()
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(
                f"{url}/auth/v1/token",
                params={"grant_type": "password"},
                headers={"apikey": key, "Content-Type": "application/json"},
                json={"email": email, "password": password},
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="No fue posible contactar el proveedor de identidad.") from exc

    if response.status_code in (400, 401, 422):
        raise HTTPException(status_code=401, detail="Correo o contraseña inválidos.")
    if response.is_error:
        raise HTTPException(status_code=502, detail="No fue posible iniciar sesión.")
    tokens = response.json()
    if not tokens.get("access_token"):
        raise HTTPException(status_code=502, detail="Respuesta de identidad incompleta.")
    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "token_type": "bearer",
        "expires_in": tokens.get("expires_in"),
    }


async def get_profile(access_token: str) -> dict:
    url, key = _config()
    headers = {"apikey": key, "Authorization": f"Bearer {access_token}"}
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            user_response = await client.get(f"{url}/auth/v1/user", headers=headers)
            if user_response.status_code in (401, 403):
                raise HTTPException(status_code=401, detail="La sesión no es válida o ha expirado.")
            if user_response.is_error:
                raise HTTPException(status_code=502, detail="Error verificando la sesión.")
            user = user_response.json()
            user_id = user.get("id")
            if not user_id:
                raise HTTPException(status_code=401, detail="No fue posible verificar la identidad.")
            profile_response = await client.get(
                f"{url}/rest/v1/profiles",
                params={"select": "id,full_name,role", "id": f"eq.{user_id}"},
                headers=headers,
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Servicio de identidad no disponible.") from exc

    if profile_response.is_error:
        raise HTTPException(status_code=502, detail="No fue posible consultar el perfil.")
    profiles = profile_response.json()
    if not isinstance(profiles, list) or len(profiles) != 1:
        raise HTTPException(status_code=403, detail="Perfil de usuario no habilitado.")
    profile = profiles[0]
    return {
        "id": user_id,
        "email": user.get("email"),
        "full_name": profile.get("full_name"),
        "role": profile["role"],
    }
