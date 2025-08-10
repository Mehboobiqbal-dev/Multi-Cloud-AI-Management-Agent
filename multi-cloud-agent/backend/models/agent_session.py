from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from models.base import BaseModel

class AgentSession(BaseModel):
    """
    Model representing an agent run/session lifecycle.
    """
    # Relationship to user
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="agent_sessions")

    # Session identifiers and state
    run_id = Column(String, unique=True, nullable=False)
    goal = Column(Text, nullable=False)
    status = Column(String, default='running')  # running, paused, completed, failed
    current_step = Column(Integer, default=0)

    # Execution history and assistance
    history = Column(Text, nullable=True)  # JSON of execution history
    awaiting_assistance = Column(Boolean, default=False)
    assistance_request = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AgentSession(id={self.id}, run_id='{self.run_id}', status='{self.status}')>"