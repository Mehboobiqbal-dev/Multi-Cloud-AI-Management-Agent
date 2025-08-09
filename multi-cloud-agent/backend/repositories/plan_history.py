from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from repositories.base import BaseRepository
from models.plan_history import PlanHistory
from schemas.plan_history import PlanHistoryCreate, PlanHistoryUpdate

class PlanHistoryRepository(BaseRepository[PlanHistory, PlanHistoryCreate, PlanHistoryUpdate]):
    """
    Repository for PlanHistory model operations.
    """
    def __init__(self, db: Session):
        super().__init__(db, PlanHistory)
    
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[PlanHistory]:
        """
        Get plan histories for a specific user with pagination.
        """
        return self.db.query(PlanHistory).filter(PlanHistory.user_id == user_id).order_by(
            PlanHistory.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def count_by_user_id(self, user_id: int) -> int:
        """
        Count plan histories for a specific user.
        """
        return self.db.query(PlanHistory).filter(PlanHistory.user_id == user_id).count()
    
    def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[PlanHistory]:
        """
        Get plan histories by status with pagination.
        """
        return self.db.query(PlanHistory).filter(PlanHistory.status == status).order_by(
            PlanHistory.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_by_date_range(self, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100) -> List[PlanHistory]:
        """
        Get plan histories within a date range with pagination.
        """
        return self.db.query(PlanHistory).filter(
            PlanHistory.created_at >= start_date,
            PlanHistory.created_at <= end_date
        ).order_by(PlanHistory.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_recent(self, days: int = 7, skip: int = 0, limit: int = 100) -> List[PlanHistory]:
        """
        Get recent plan histories with pagination.
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(PlanHistory).filter(
            PlanHistory.created_at >= start_date
        ).order_by(PlanHistory.created_at.desc()).offset(skip).limit(limit).all()
    
    def update_status(self, plan_id: int, status: str) -> PlanHistory:
        """
        Update the status of a plan history.
        """
        plan = self.get_or_404(plan_id)
        plan.status = status
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan
    
    def update_execution_results(self, plan_id: int, execution_results: str) -> PlanHistory:
        """
        Update the execution results of a plan history.
        """
        plan = self.get_or_404(plan_id)
        plan.execution_results = execution_results
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan
    
    def update_final_result(self, plan_id: int, final_result: str) -> PlanHistory:
        """
        Update the final result of a plan history.
        """
        plan = self.get_or_404(plan_id)
        plan.final_result = final_result
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan
    
    def add_feedback(self, plan_id: int, feedback: str, correction: Optional[str] = None) -> PlanHistory:
        """
        Add feedback to a plan history.
        """
        plan = self.get_or_404(plan_id)
        plan.feedback = feedback
        plan.correction = correction
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan