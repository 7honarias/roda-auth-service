import uuid
from sqlalchemy import UUID, Boolean, Column, DateTime, String
from sqlalchemy.sql import func
from app.models import Base



class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_ip = Column(String(45), nullable=True)
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id})>"