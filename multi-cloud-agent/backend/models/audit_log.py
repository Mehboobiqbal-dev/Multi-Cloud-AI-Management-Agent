from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship

from models.base import BaseModel

class AuditLog(BaseModel):
    """
    Model for storing audit logs of user actions.
    """
    # Relationship to user (nullable for system actions)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user = relationship("User", back_populates="audit_logs")
    
    # Audit information
    action = Column(String, nullable=False)  # The action performed (e.g., "login", "create_resource")
    resource_type = Column(String, nullable=True)  # Type of resource affected (e.g., "user", "vm")
    resource_id = Column(String, nullable=True)  # ID of the resource affected
    ip_address = Column(String, nullable=True)  # IP address of the user
    user_agent = Column(String, nullable=True)  # User agent of the client
    details = Column(Text, nullable=True)  # Additional details as JSON string
    status = Column(String, nullable=False, default="success")  # success, failure
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', status='{self.status}')>"