from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship

from models.base import BaseModel

class PlanHistory(BaseModel):
    """
    Model for storing execution plans and their history.
    """
    # Relationship to user
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="plan_histories")
    
    # Plan information
    prompt = Column(Text, nullable=False)  # The original user prompt
    plan = Column(Text, nullable=False)  # JSON string of the execution plan
    status = Column(String, nullable=False)  # pending, running, completed, failed, requires_feedback
    
    # Execution results
    execution_results = Column(Text, nullable=True)  # JSON string of execution steps and results
    final_result = Column(Text, nullable=True)  # Final result or output
    
    # Feedback information
    feedback = Column(String, nullable=True)  # User feedback (positive, negative)
    correction = Column(Text, nullable=True)  # User correction or additional information
    
    def __repr__(self) -> str:
        return f"<PlanHistory(id={self.id}, status='{self.status}')>"