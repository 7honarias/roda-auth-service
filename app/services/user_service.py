from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from app.repositories import UserRepository
from app.schemas.user import UserResponse, UserProfileResponse, UserUpdateRequest, PaginatedResponse, UserStatus
from app.utils.audit import AuditLogger


class UserService:
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def get_user_profile(self, user_id: str) -> Tuple[bool, str, Optional[UserProfileResponse]]:
        try:
            user = self.user_repo.get_user_by_id(user_id)
            if not user:
                return False, "Usuario no encontrado", None
            
            profile_data = user.__dict__.copy()
            if 'document_front_url' in profile_data:
                profile_data.pop('document_front_url', None)
            if 'document_back_url' in profile_data:
                profile_data.pop('document_back_url', None)
            
            profile_response = UserProfileResponse(**profile_data)
            return True, "Perfil obtenido exitosamente", profile_response
            
        except Exception as e:
            return False, f"Error obteniendo perfil: {str(e)}", None
    
    def get_user_full_data(self, user_id: str, requesting_user_id: str, requesting_user_role: str) -> Tuple[bool, str, Optional[UserResponse]]:
        try:
            if user_id != requesting_user_id and requesting_user_role != "admin":
                return False, "No autorizado para ver estos datos", None
            
            user = self.user_repo.get_user_by_id(user_id)
            if not user:
                return False, "Usuario no encontrado", None
            
            user_response = UserResponse.from_orm(user)
            return True, "Usuario obtenido exitosamente", user_response
            
        except Exception as e:
            return False, f"Error obteniendo usuario: {str(e)}", None
    
    def update_user_profile(
        self, 
        user_id: str, 
        update_data: UserUpdateRequest,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[UserProfileResponse]]:
        try:
            existing_user = self.user_repo.get_user_by_id(user_id)
            if not existing_user:
                return False, "Usuario no encontrado", None
            
            if update_data.cedula and self.user_repo.check_cedula_exists(update_data.cedula, exclude_user_id=user_id):
                return False, "La cédula ya está registrada", None
            
            user_dict = update_data.dict(exclude_unset=True)
            updated_user = self.user_repo.update_user(user_id, user_dict)
            
            if not updated_user:
                return False, "Error actualizando usuario", None
            
            AuditLogger.log_action(
                user_id=user_id,
                action="profile_update",
                resource="user",
                details={"updated_fields": list(user_dict.keys())},
                ip_address=ip_address
            )
            
            profile_response = UserProfileResponse.from_orm(updated_user)
            return True, "Perfil actualizado exitosamente", profile_response
            
        except Exception as e:
            return False, f"Error actualizando perfil: {str(e)}", None
    
    def update_user_images(
        self, 
        user_id: str, 
        image_urls: dict,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[UserResponse]]:
        """Actualizar URLs de imágenes del usuario"""
        try:
            user = self.user_repo.get_user_by_id(user_id)
            if not user:
                return False, "Usuario no encontrado", None
            
            update_data = {}
            for field, url in image_urls.items():
                if field in ['profile_photo_url', 'document_front_url', 'document_back_url']:
                    update_data[field] = url
            
            if not update_data:
                return False, "No hay imágenes para actualizar", None
            
            updated_user = self.user_repo.update_user(user_id, update_data)
            
            if not updated_user:
                return False, "Error actualizando imágenes", None
            
            AuditLogger.log_action(
                user_id=user_id,
                action="images_update",
                resource="user",
                details={"updated_images": list(image_urls.keys())},
                ip_address=ip_address
            )
            
            user_response = UserResponse.from_orm(updated_user)
            return True, "Imágenes actualizadas exitosamente", user_response
            
        except Exception as e:
            return False, f"Error actualizando imágenes: {str(e)}", None
    
    def verify_user(self, user_id: str, admin_user_id: str, ip_address: Optional[str] = None) -> Tuple[bool, str, Optional[UserResponse]]:
        """Verificar usuario (solo admin)"""
        try:
            user = self.user_repo.get_user_by_id(user_id)
            if not user:
                return False, "Usuario no encontrado", None
            
            verified_user = self.user_repo.verify_user(user_id)
            
            if not verified_user:
                return False, "Error verificando usuario", None
            
            AuditLogger.log_action(
                user_id=user_id,
                action="user_verification",
                resource="user",
                details={"verified_by": admin_user_id},
                ip_address=ip_address
            )
            
            user_response = UserResponse.from_orm(verified_user)
            return True, "Usuario verificado exitosamente", user_response
            
        except Exception as e:
            return False, f"Error verificando usuario: {str(e)}", None
    
    def update_user_status(
        self, 
        user_id: str, 
        status: UserStatus, 
        admin_user_id: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[UserResponse]]:
        try:
            user = self.user_repo.get_user_by_id(user_id)
            if not user:
                return False, "Usuario no encontrado", None
            
            updated_user = self.user_repo.update_user_status(user_id, status)
            
            if not updated_user:
                return False, "Error actualizando estado", None
            
            AuditLogger.log_action(
                user_id=user_id,
                action="status_update",
                resource="user",
                details={
                    "new_status": status.value,
                    "updated_by": admin_user_id
                },
                ip_address=ip_address
            )
            
            user_response = UserResponse.from_orm(updated_user)
            return True, "Estado actualizado exitosamente", user_response
            
        except Exception as e:
            return False, f"Error actualizando estado: {str(e)}", None
    
    def list_users(
        self, 
        page: int = 1, 
        per_page: int = 20,
        status: Optional[UserStatus] = None,
        role: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[bool, str, Optional[PaginatedResponse]]:
        try:
            result = self.user_repo.list_users(
                page=page,
                per_page=per_page,
                status=status,
                role=role,
                search=search
            )
            
            users_response = [UserResponse.from_orm(user) for user in result["items"]]
            
            paginated_response = PaginatedResponse(
                items=users_response,
                total=result["total"],
                page=result["page"],
                per_page=result["per_page"],
                pages=result["pages"]
            )
            
            return True, "Usuarios obtenidos exitosamente", paginated_response
            
        except Exception as e:
            return False, f"Error listando usuarios: {str(e)}", None
    
    def delete_user(self, user_id: str, admin_user_id: str, ip_address: Optional[str] = None) -> Tuple[bool, str]:
        try:
            user = self.user_repo.get_user_by_id(user_id)
            if not user:
                return False, "Usuario no encontrado"
            
            success = self.user_repo.delete_user(user_id)
            if not success:
                return False, "Error eliminando usuario"
            
            AuditLogger.log_action(
                user_id=user_id,
                action="user_deletion",
                resource="user",
                details={"deleted_by": admin_user_id},
                ip_address=ip_address
            )
            
            return True, "Usuario eliminado exitosamente"
            
        except Exception as e:
            return False, f"Error eliminando usuario: {str(e)}"