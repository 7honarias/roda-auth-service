from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.config.settings import settings
from app.database import get_db
from app.schemas.user import (
    UserRegisterRequest, 
    UserLoginRequest, 
    TokenResponse, 
    RefreshTokenRequest,
    ApiResponse
)
from app.services.auth_service import AuthService
from app.utils.audit import AuditLogger

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Obtener usuario actual desde token JWT"""
    auth_service = AuthService(db)
    
    is_valid, message, token_data = auth_service.verify_token(credentials.credentials)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


@router.post("/register", response_model=ApiResponse, summary="Registrar nuevo usuario")
async def register_user(
    request: Request,
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registrar nuevo usuario con:
    - Datos personales (nombres, apellidos, cédula, teléfono, dirección)
    - Contraseña segura
    - Foto de perfil y documentos se subirán por separado
    """
    try:
        auth_service = AuthService(db)
        
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        success, message, data = auth_service.register_user(
            user_data=user_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return ApiResponse(
            success=True,
            message=message,
            data=data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/login", response_model=ApiResponse, summary="Login de usuario")
async def login_user(
    request: Request,
    login_data: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login de usuario con cédula y contraseña
    Retorna access token y refresh token
    """
    try:
        auth_service = AuthService(db)
        
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        success, message, token_response = auth_service.login_user(
            login_data=login_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=message
            )
        
        return ApiResponse(
            success=True,
            message=message,
            data=token_response.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/refresh", response_model=ApiResponse, summary="Renovar access token")
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Renovar access token usando refresh token
    """
    try:
        auth_service = AuthService(db)
        
        ip_address = request.client.host if request.client else None
        
        success, message, token_response = auth_service.refresh_access_token(
            refresh_token=refresh_data.refresh_token,
            ip_address=ip_address
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=message
            )
        
        return ApiResponse(
            success=True,
            message=message,
            data=token_response.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/logout", response_model=ApiResponse, summary="Logout de usuario")
async def logout_user(
    request: Request,
    refresh_data: Optional[RefreshTokenRequest] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout de usuario
    Revoca refresh token y marca sesión como cerrada
    """
    try:
        auth_service = AuthService(db)
        
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de acceso requerido"
            )
        
        access_token = auth_header.split(" ")[1]
        refresh_token = refresh_data.refresh_token if refresh_data else None
        
        ip_address = request.client.host if request.client else None
        
        success, message = auth_service.logout_user(
            access_token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return ApiResponse(
            success=True,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/verify-token", response_model=ApiResponse, summary="Verificar token")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """
    Verificar si el token de acceso es válido
    """
    try:
        return ApiResponse(
            success=True,
            message="Token válido",
            data={
                "user_id": current_user.get("sub"),
                "cedula": current_user.get("cedula"),
                "role": current_user.get("role"),
                "exp": current_user.get("exp")
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )