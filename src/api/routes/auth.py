from fastapi import APIRouter, HTTPException, status

from src.api.core.security import create_access_token
from src.api.schemas.auth import LoginRequest, TokenResponse
from src.api.services import auth_service

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
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
