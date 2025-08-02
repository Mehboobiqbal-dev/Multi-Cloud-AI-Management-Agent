from models import AuditLog

def log_audit(db, user_id, action, details):
    log = AuditLog(user_id=user_id, action=action, details=details)
    db.add(log)
    db.commit()
