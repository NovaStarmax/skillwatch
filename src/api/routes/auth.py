from fastapi import APIRouter, HTTPException, status

from src.api.core.security import create_access_token
from src.api.schemas.auth import LoginRequest, TokenResponse
from src.api.services import auth_service

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtenir un token JWT",
    description="""Authentification par username/password.
Retourne un token Bearer valable 30 minutes.

Credentials configurés via les variables d'env `ADMIN_USERNAME` / `ADMIN_PASSWORD`.

Utilisation : `Authorization: Bearer {token}`""",
    responses={401: {"description": "Identifiants incorrects"}},
)
def login(body: LoginRequest):
    user = auth_service.authenticate_user(body.username, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": user["username"]})
    return TokenResponse(access_token=token)
