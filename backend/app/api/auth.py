from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

from backend.app.services.supabase_auth import (
    get_profile, login_with_password, signup_with_password, change_evaluator_role,
)


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
    can_switch_roles: bool = False


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(min_length=8, max_length=128)

    @field_validator("full_name", "email", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class RegisterResponse(BaseModel):
    message: str
    requires_confirmation: bool


class EvaluatorRoleRequest(BaseModel):
    role: str = Field(pattern="^(cliente|especialista_tecnico|logistica|aplicador|calidad)$")


class EvaluatorRoleResponse(BaseModel):
    role: str
    enabled: bool



@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(payload: RegisterRequest):
    # El servidor nunca acepta un rol enviado en el registro.
    return await signup_with_password(payload.email.lower(), payload.password, payload.full_name)


@router.post("/evaluator/role", response_model=EvaluatorRoleResponse)
async def set_evaluator_role(
    payload: EvaluatorRoleRequest,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión.")
    return await change_evaluator_role(credentials.credentials, payload.role)


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    return await login_with_password(payload.email, payload.password)


@router.get("/me", response_model=UserProfile)
async def me(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Debes iniciar sesión.")
    return await get_profile(credentials.credentials)
