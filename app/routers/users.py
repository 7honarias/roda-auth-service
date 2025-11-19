from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.config.settings import settings
from app.database import get_db
from app.schemas.user import (
    UserUpdateRequest, 
    ApiResponse, 
    UserStatus
)
from app.services.user_service import UserService
from app.services.file_service import FileService

router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer()


def get_current_user_data(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Obtener datos del usuario actual desde token JWT"""
    from app.services.auth_service import AuthService
    
    auth_service = AuthService(db)
    is_valid, message, token_data = auth_service.verify_token(credentials.credentials)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


def require_admin(current_user: dict = Depends(get_current_user_data)):
    """Requerir rol de administrador"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de administrador"
        )
    return current_user


@router.get("/me", response_model=ApiResponse, summary="Obtener perfil del usuario actual")
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user_data),
    db: Session = Depends(get_db)
):
    """
    Obtener perfil del usuario autenticado
    """
    try:
        user_service = UserService(db)
        
        success, message, profile = user_service.get_user_profile(current_user["sub"])
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message
            )
        
        return ApiResponse(
            success=True,
            message=message,
            data=profile.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.put("/me", response_model=ApiResponse, summary="Actualizar perfil del usuario")
async def update_current_user_profile(
    request: Request,
    update_data: UserUpdateRequest,
    current_user: dict = Depends(get_current_user_data),
    db: Session = Depends(get_db)
):
    """
    Actualizar datos del perfil del usuario actual
    """
    try:
        user_service = UserService(db)
        
        ip_address = request.client.host if request.client else None
        
        success, message, profile = user_service.update_user_profile(
            user_id=current_user["sub"],
            update_data=update_data,
            ip_address=ip_address
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return ApiResponse(
            success=True,
            message=message,
            data=profile.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/me/upload-photos", response_model=ApiResponse, summary="Subir fotos de usuario")
async def upload_user_photos(
    request: Request,
    profile_photo: Optional[UploadFile] = File(None, description="Foto de perfil"),
    document_front: Optional[UploadFile] = File(None, description="Documento de identidad frontal"),
    document_back: Optional[UploadFile] = File(None, description="Documento de identidad posterior"),
    current_user: dict = Depends(get_current_user_data),
    db: Session = Depends(get_db)
):
    """
    Subir fotos de perfil y documentos de identidad
    """
    try:
        if not profile_photo and not document_front and not document_back:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se debe subir al menos una imagen"
            )
        
        ip_address = request.client.host if request.client else None
        
        files_to_upload = []
        if profile_photo:
            is_valid, message = FileService.validate_file_upload(profile_photo)
            if not is_valid:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
            files_to_upload.append(("profile_photo", profile_photo))
        
        if document_front:
            is_valid, message = FileService.validate_file_upload(document_front)
            if not is_valid:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
            files_to_upload.append(("document_front", document_front))
        
        if document_back:
            is_valid, message = FileService.validate_file_upload(document_back)
            if not is_valid:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
            files_to_upload.append(("document_back", document_back))
        
        success, message, urls = await FileService.upload_document_images(
            profile_photo=profile_photo,
            document_front=document_front,
            document_back=document_back,
            user_id=current_user["sub"],
            ip_address=ip_address
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        user_service = UserService(db)
        success, message, updated_user = user_service.update_user_images(
            user_id=current_user["sub"],
            image_urls=urls,
            ip_address=ip_address
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return ApiResponse(
            success=True,
            message="Fotos subidas exitosamente",
            data={
                "uploaded_files": urls,
                "user": updated_user.dict()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/{user_id}", response_model=ApiResponse, summary="Obtener usuario por ID")
async def get_user_by_id(
    user_id: str,
    current_user: dict = Depends(get_current_user_data),
    db: Session = Depends(get_db)
):
    """
    Obtener datos completos de un usuario
    Solo disponible para el mismo usuario o administradores
    """
    try:
        user_service = UserService(db)
        
        success, message, user = user_service.get_user_full_data(
            user_id=user_id,
            requesting_user_id=current_user["sub"],
            requesting_user_role=current_user["role"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message
            )
        
        return ApiResponse(
            success=True,
            message=message,
            data=user.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.put("/{user_id}/status", response_model=ApiResponse, summary="Actualizar estado de usuario")
async def update_user_status(
    request: Request,
    user_id: str,
    status: UserStatus,
    current_admin: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Actualizar estado de un usuario (solo administradores)
    """
    try:
        user_service = UserService(db)
        
        ip_address = request.client.host if request.client else None
        
        success, message, user = user_service.update_user_status(
            user_id=user_id,
            status=status,
            admin_user_id=current_admin["sub"],
            ip_address=ip_address
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return ApiResponse(
            success=True,
            message=message,
            data=user.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/{user_id}/verify", response_model=ApiResponse, summary="Verificar usuario")
async def verify_user(
    request: Request,
    user_id: str,
    current_admin: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Verificar un usuario (solo administradores)
    """
    try:
        user_service = UserService(db)
        
        ip_address = request.client.host if request.client else None
        
        success, message, user = user_service.verify_user(
            user_id=user_id,
            admin_user_id=current_admin["sub"],
            ip_address=ip_address
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return ApiResponse(
            success=True,
            message=message,
            data=user.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.delete("/{user_id}", response_model=ApiResponse, summary="Eliminar usuario")
async def delete_user(
    request: Request,
    user_id: str,
    current_admin: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Eliminar un usuario (soft delete - solo administradores)
    """
    try:
        user_service = UserService(db)
        
        ip_address = request.client.host if request.client else None
        
        success, message = user_service.delete_user(
            user_id=user_id,
            admin_user_id=current_admin["sub"],
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


@router.get("/", response_model=ApiResponse, summary="Listar usuarios")
async def list_users(
    page: int = 1,
    per_page: int = 20,
    status: Optional[UserStatus] = None,
    role: Optional[str] = None,
    search: Optional[str] = None,
    current_admin: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Listar usuarios con filtros (solo administradores)
    """
    try:
        user_service = UserService(db)
        
        success, message, paginated_response = user_service.list_users(
            page=page,
            per_page=per_page,
            status=status,
            role=role,
            search=search
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return ApiResponse(
            success=True,
            message=message,
            data=paginated_response.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )
