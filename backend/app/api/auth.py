from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from backend.app.services.supabase_auth import get_profile, login_with_password


router = APIRouter(prefix="/auth", tags=["Autenticación"])
bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None


class UserProfile(BaseModel):
    id: str
    email: str | None = None
    full_name: str | None = None
    role: str


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    return await login_with_password(payload.email, payload.password)


@router.get("/me", response_model=UserProfile)
async def me(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Debes iniciar sesión.")
    return await get_profile(credentials.credentials)
