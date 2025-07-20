from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()
<<<<<<< HEAD

=======
 
>>>>>>> 7ff0246737b430c27cbcaf82f365a8e84606a58f
class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship('User')

def log_audit(db, user_id, action, details):
    log = AuditLog(user_id=user_id, action=action, details=details)
    db.add(log)
<<<<<<< HEAD
    db.commit()
=======
    db.commit()
>>>>>>> 7ff0246737b430c27cbcaf82f365a8e84606a58f
