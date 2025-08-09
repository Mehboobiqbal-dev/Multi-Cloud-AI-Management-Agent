from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from repositories.base import BaseRepository
from models.audit_log import AuditLog
from schemas.audit_log import AuditLogCreate, AuditLogBase

class AuditLogRepository(BaseRepository[AuditLog, AuditLogCreate, AuditLogBase]):
    """
    Repository for AuditLog model operations.
    """
    def __init__(self, db: Session):
        super().__init__(db, AuditLog)
    
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """
        Get audit logs for a specific user with pagination.
        """
        return self.db.query(AuditLog).filter(AuditLog.user_id == user_id).order_by(
            AuditLog.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def count_by_user_id(self, user_id: int) -> int:
        """
        Count audit logs for a specific user.
        """
        return self.db.query(AuditLog).filter(AuditLog.user_id == user_id).count()
    
    def get_by_action(self, action: str, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """
        Get audit logs for a specific action with pagination.
        """
        return self.db.query(AuditLog).filter(AuditLog.action == action).order_by(
            AuditLog.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_by_resource(self, resource_type: str, resource_id: str, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """
        Get audit logs for a specific resource with pagination.
        """
        return self.db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        ).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """
        Get audit logs by status with pagination.
        """
        return self.db.query(AuditLog).filter(AuditLog.status == status).order_by(
            AuditLog.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_by_date_range(self, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """
        Get audit logs within a date range with pagination.
        """
        return self.db.query(AuditLog).filter(
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        ).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_recent(self, days: int = 7, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """
        Get recent audit logs with pagination.
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(AuditLog).filter(
            AuditLog.created_at >= start_date
        ).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    def create_log(
        self, action: str, user_id: Optional[int] = None, resource_type: Optional[str] = None,
        resource_id: Optional[str] = None, ip_address: Optional[str] = None,
        user_agent: Optional[str] = None, details: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ) -> AuditLog:
        """
        Create a new audit log entry.
        """
        db_obj = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            status=status
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj