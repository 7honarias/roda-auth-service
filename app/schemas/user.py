from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """Roles de usuario"""
    CUSTOMER = "customer"
    ADMIN = "admin"
    AGENT = "agent"


class UserStatus(str, Enum):
    """Estados de usuario"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class UserBase(BaseModel):
    """Schema base para usuario"""
    cedula: str = Field(..., min_length=6, max_length=20, description="Cédula de identidad")
    first_name: str = Field(..., min_length=1, max_length=100, description="Nombres")
    last_name: str = Field(..., min_length=1, max_length=100, description="Apellidos")
    phone: str = Field(..., min_length=7, max_length=20, description="Teléfono")
    address: str = Field(..., min_length=10, max_length=500, description="Dirección")
    
    @validator('cedula')
    def validate_cedula(cls, v):
        cedula_clean = v.replace('-', '').replace(' ', '')
        if not cedula_clean.isdigit():
            raise ValueError('La cédula debe contener solo números')
        return cedula_clean
    
    @validator('phone')
    def validate_phone(cls, v):
        phone_clean = v.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
        if not phone_clean.isdigit() or len(phone_clean) < 7:
            raise ValueError('Formato de teléfono inválido')
        return phone_clean


class UserRegisterRequest(UserBase):
    """Schema para registro de usuario"""
    password: str = Field(..., min_length=8, max_length=128, description="Contraseña")
    confirm_password: str = Field(..., description="Confirmación de contraseña")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Las contraseñas no coinciden')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v


class UserLoginRequest(BaseModel):
    """Schema para login de usuario"""
    cedula: str = Field(..., description="Cédula de identidad")
    password: str = Field(..., description="Contraseña")


class UserResponse(BaseModel):
    """Schema para respuesta de usuario"""
    id: UUID
    cedula: str
    first_name: str
    last_name: str
    phone: str
    address: str
    role: UserRole
    status: UserStatus
    is_verified: bool
    profile_photo_url: Optional[str] = None
    document_front_url: Optional[str] = None
    document_back_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Schema para perfil de usuario"""
    id: UUID
    cedula: str
    first_name: str
    last_name: str
    phone: str
    address: str
    role: UserRole
    status: UserStatus
    is_verified: bool
    profile_photo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema para respuesta de tokens"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int  # en segundos


class RefreshTokenRequest(BaseModel):
    """Schema para solicitud de refresh token"""
    refresh_token: str


class FileUploadResponse(BaseModel):
    """Schema para respuesta de subida de archivos"""
    filename: str
    url: str
    content_type: str
    size: int


class ApiResponse(BaseModel):
    """Schema para respuestas de API genéricas"""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Schema para respuestas paginadas"""
    items: list
    total: int
    page: int
    per_page: int
    pages: int


class UserUpdateRequest(BaseModel):
    """Schema para actualización de usuario"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, min_length=7, max_length=20)
    address: Optional[str] = Field(None, min_length=10, max_length=500)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            phone_clean = v.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
            if not phone_clean.isdigit() or len(phone_clean) < 7:
                raise ValueError('Formato de teléfono inválido')
        return v