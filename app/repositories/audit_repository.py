
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

from app.models.audit_model import AuditLog


class AuditRepository:
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_audit_log(self, audit_data: dict) -> AuditLog:
        audit_log = AuditLog(**audit_data)
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log
    
    def get_audit_logs(
        self, 
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> dict:
        query = self.db.query(AuditLog)
        
        if user_id:
            try:
                uuid_user_id = UUID(user_id)
                query = query.filter(AuditLog.user_id == uuid_user_id)
            except ValueError:
                pass
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        query = query.order_by(AuditLog.created_at.desc())
        
        total = query.count()
        
        offset = (page - 1) * per_page
        logs = query.offset(offset).limit(per_page).all()
        
        return {
            "items": logs,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    
    def get_user_activity_summary(self, user_id: str, days: int = 30) -> dict:
        """Obtener resumen de actividad del usuario"""
        try:
            uuid_user_id = UUID(user_id)
        except ValueError:
            return {"error": "ID de usuario inválido"}
        
        actions_query = self.db.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.user_id == uuid_user_id,
            AuditLog.created_at >= func.now() - func.cast(f"{days} days", func.interval)
        ).group_by(AuditLog.action)
        
        actions = actions_query.all()
        action_summary = {action: count for action, count in actions}
        
        last_activity = self.db.query(AuditLog.created_at).filter(
            AuditLog.user_id == uuid_user_id
        ).order_by(AuditLog.created_at.desc()).first()
        
        return {
            "user_id": user_id,
            "period_days": days,
            "action_summary": action_summary,
            "last_activity": last_activity[0] if last_activity else None,
            "total_actions": sum(action_summary.values())
        }
    
    def get_system_activity_summary(self, days: int = 7) -> dict:
        """Obtener resumen de actividad del sistema"""
        actions_query = self.db.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.created_at >= func.now() - func.cast(f"{days} days", func.interval)
        ).group_by(AuditLog.action)
        
        actions = actions_query.all()
        action_summary = {action: count for action, count in actions}
        
        daily_query = self.db.query(
            func.date(AuditLog.created_at).label('date'),
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.created_at >= func.now() - func.cast(f"{days} days", func.interval)
        ).group_by(func.date(AuditLog.created_at)).order_by('date')
        
        daily_activity = [
            {"date": str(date), "count": count} 
            for date, count in daily_query.all()
        ]
        
        return {
            "period_days": days,
            "action_summary": action_summary,
            "daily_activity": daily_activity,
            "total_actions": sum(action_summary.values())
        }