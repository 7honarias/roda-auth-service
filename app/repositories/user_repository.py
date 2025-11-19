"""
Repositorio para gestión de usuarios
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from app.models.refresh_token_model import RefreshToken
from app.models.status_enum import UserStatus
from app.models.user_model import User
from app.utils.security import get_password_hash, verify_password
from uuid import UUID


class UserRepository:
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: dict) -> User:
        user_data['password_hash'] = get_password_hash(user_data.pop('confirm_password'))
        
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_by_cedula(self, cedula: str) -> Optional[User]:
        return self.db.query(User).filter(User.cedula == cedula).first()
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        try:
            uuid_user_id = user_id
            return self.db.query(User).filter(User.id == uuid_user_id).first()
        except ValueError:
            return None
    
    def authenticate_user(self, cedula: str, password: str) -> Optional[User]:
        user = self.get_user_by_cedula(cedula)
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    def update_user(self, user_id: str, update_data: dict) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        protected_fields = ['id', 'cedula', 'password_hash', 'role', 'status', 'created_at']
        for field in protected_fields:
            update_data.pop(field, None)
        
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = user.updated_at
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_user_status(self, user_id: str, status: UserStatus) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.status = status
        user.updated_at = user.updated_at
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def verify_user(self, user_id: str) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.is_verified = True
        user.status = UserStatus.ACTIVE
        user.updated_at = user.updated_at
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_last_login(self, user_id: str):
        user = self.get_user_by_id(user_id)
        if user:
            user.last_login = user.updated_at
            self.db.commit()
    
    def delete_user(self, user_id: str) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.status = UserStatus.INACTIVE
        user.updated_at = user.updated_at
        
        self.db.commit()
        return True
    
    def list_users(
        self, 
        page: int = 1, 
        per_page: int = 20,
        status: Optional[UserStatus] = None,
        role: Optional[str] = None,
        search: Optional[str] = None
    ) -> dict:
        query = self.db.query(User)
        
        if status:
            query = query.filter(User.status == status)
        
        if role:
            query = query.filter(User.role == role)
        
        if search:
            search_filter = or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.cedula.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        total = query.count()
        
        offset = (page - 1) * per_page
        users = query.offset(offset).limit(per_page).all()
        
        return {
            "items": users,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    
    def check_cedula_exists(self, cedula: str, exclude_user_id: Optional[str] = None) -> bool:
        query = self.db.query(User).filter(User.cedula == cedula)
        
        if exclude_user_id:
            try:
                uuid_exclude = UUID(exclude_user_id)
                query = query.filter(User.id != uuid_exclude)
            except ValueError:
                pass
        
        return self.db.query(query.exists()).scalar()


class RefreshTokenRepository:
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_refresh_token(self, token_data: dict) -> RefreshToken:
        """Crear refresh token"""
        refresh_token = RefreshToken(**token_data)
        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)
        return refresh_token
    
    def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        return self.db.query(RefreshToken).filter(
            and_(
                RefreshToken.token == token,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > func.now()
            )
        ).first()
    
    def revoke_refresh_token(self, token: str) -> bool:
        refresh_token = self.db.query(RefreshToken).filter(
            RefreshToken.token == token
        ).first()
        
        if refresh_token:
            refresh_token.is_revoked = True
            self.db.commit()
            return True
        
        return False
    
    