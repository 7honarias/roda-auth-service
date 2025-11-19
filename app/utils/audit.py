import logging
import json
from typing import Optional
from app.config.settings import settings


class AuditLogger:
    
    @staticmethod
    def log_action(
        user_id: Optional[str],
        action: str,
        resource: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        try:
            from app.repositories.audit_repository import AuditRepository
            from app.models import AuditLog
            
            audit_data = {
                "user_id": user_id,
                "action": action,
                "resource": resource,
                "details": json.dumps(details) if details else None,
                "ip_address": ip_address,
                "user_agent": user_agent
            }
            
            audit_repo = AuditRepository()
            audit_repo.create_audit_log(audit_data)
            
        except Exception as e:
            logging.error(f"Error registrando auditoría: {e}")


class AppLogger:
    
    @staticmethod
    def setup_logging():
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('app.log'),
                logging.StreamHandler()
            ]
        )
        
        app_logger = logging.getLogger('roda_auth')
        return app_logger


def setup_app_logging():
    return AppLogger.setup_logging()