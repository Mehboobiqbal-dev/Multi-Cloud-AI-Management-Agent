from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import BaseModel

class ChatHistory(BaseModel):
    """
    Model for storing chat messages between users and the agent.
    """
    # Relationship to user
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="chat_messages")
    
    # Message information
    sender = Column(String, nullable=False)  # 'user' or 'agent'
    message = Column(Text, nullable=False)
    message_type = Column(String, default='text')  # 'text', 'command', 'assistance'
    agent_run_id = Column(String, nullable=True)  # Link to specific agent run
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<ChatHistory(id={self.id}, sender='{self.sender}', message_type='{self.message_type}')>"