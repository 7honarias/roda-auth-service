"""
Servicio de autenticación
"""
from typing import Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.repositories import UserRepository, RefreshTokenRepository
from app.schemas.user import UserRegisterRequest, UserLoginRequest, TokenResponse
from app.utils.security import create_access_token, create_refresh_token, verify_token
from app.utils.audit import AuditLogger
from app.config.settings import settings


class AuthService:
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.refresh_repo = RefreshTokenRepository(db)
    
    def register_user(self, user_data: UserRegisterRequest, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Tuple[bool, str, Optional[dict]]:
        try:
            if self.user_repo.check_cedula_exists(user_data.cedula):
                return False, "La cédula ya está registrada", None
            
            user_dict = user_data.model_dump(exclude={"password"})
            
            user = self.user_repo.create_user(user_dict)
            
            AuditLogger.log_action(
                user_id=str(user.id),
                action="register",
                resource="user",
                details={"cedula": user.cedula},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return True, "Usuario registrado exitosamente", {"user_id": str(user.id)}
            
        except Exception as e:
            return False, f"Error registrando usuario: {str(e)} {str(user_dict)}", None
    
    def login_user(self, login_data: UserLoginRequest, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Tuple[bool, str, Optional[TokenResponse]]:
        try:
            user = self.user_repo.authenticate_user(login_data.cedula, login_data.password)
            
            if not user:
                AuditLogger.log_action(
                    user_id=None,
                    action="login_failed",
                    resource="user",
                    details={"cedula": login_data.cedula},
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return False, "Cédula o contraseña incorrecta", None
            
            
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": str(user.id), "cedula": user.cedula, "role": user.role.value},
                expires_delta=access_token_expires
            )
            
            refresh_token = create_refresh_token(data={"sub": str(user.id)})
            
            token_data = {
                "user_id": user.id,
                "token": refresh_token,
                "expires_at": datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
                "created_by_ip": ip_address
            }
            
            self.refresh_repo.create_refresh_token(token_data)
            
            self.user_repo.update_last_login(str(user.id))
            
            AuditLogger.log_action(
                user_id=str(user.id),
                action="login",
                resource="user",
                details={"cedula": user.cedula},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            token_response = TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
            return True, "Login exitoso", token_response
            
        except Exception as e:
            return False, f"Error en login: {str(e)}", None
    
    def refresh_access_token(self, refresh_token: str, ip_address: Optional[str] = None) -> Tuple[bool, str, Optional[TokenResponse]]:
        try:
            token_data = verify_token(refresh_token, "refresh")
            if not token_data:
                return False, "Refresh token inválido o expirado", None
            
            stored_token = self.refresh_repo.get_refresh_token(refresh_token)
            if not stored_token:
                return False, "Refresh token no encontrado", None
            
            user = self.user_repo.get_user_by_id(token_data.get("sub"))
            if not user:
                return False, "Usuario no encontrado", None
            
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            new_access_token = create_access_token(
                data={"sub": str(user.id), "cedula": user.cedula, "role": user.role.value},
                expires_delta=access_token_expires
            )
            
            new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
            
            self.refresh_repo.revoke_refresh_token(refresh_token)
            token_data = {
                "user_id": user.id,
                "token": new_refresh_token,
                "expires_at": datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
                "created_by_ip": ip_address
            }
            
            self.refresh_repo.create_refresh_token(token_data)
            
            token_response = TokenResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
            return True, "Token renovado exitosamente", token_response
            
        except Exception as e:
            return False, f"Error renovando token: {str(e)}", None
    
    def logout_user(self, access_token: str, refresh_token: Optional[str] = None, ip_address: Optional[str] = None) -> Tuple[bool, str]:
        try:
            token_data = verify_token(access_token, "access")
            if not token_data:
                return False, "Token inválido"
            
            user_id = token_data.get("sub")
            
            if refresh_token:
                self.refresh_repo.revoke_refresh_token(refresh_token)
            
            
            AuditLogger.log_action(
                user_id=user_id,
                action="logout",
                resource="user",
                ip_address=ip_address
            )
            
            return True, "Logout exitoso"
            
        except Exception as e:
            return False, f"Error en logout: {str(e)}"
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[str], Optional[dict]]:
        try:
            token_data = verify_token(token, "access")
            if not token_data:
                return False, "Token inválido o expirado", None
            
            user_id = token_data.get("sub")
            user = self.user_repo.get_user_by_id(user_id)
            
            if not user:
                return False, "Usuario no encontrado", None
            
            return True, "Token válido", token_data
            
        except Exception as e:
            return False, f"Error verificando token: {str(e)}", None