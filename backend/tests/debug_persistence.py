import logging
import sys
from uuid import uuid4
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.citizen import CitizenService
from app.schemas.citizen import CitizenCreateRequest
from app.observability.models import AuditLog, AuditAction

# Enable logging to see SQLAlchemy internal errors
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger("sqlalchemy.engine")
logger.setLevel(logging.INFO)

db = SessionLocal()

try:
    print("--- PRE-CHECK ---")
    log_count = db.query(AuditLog).count()
    print(f"Initial logs: {log_count}")

    print("\n--- TRIGGER ACTION ---")
    service = CitizenService(db)
    payload = CitizenCreateRequest(
        name=f"Debug User {uuid4().hex[:4]}",
        contact_number="9876543210",
        ward="Ward-1"
    )
    citizen = service.create_citizen(payload)
    print(f"Citizen created: {citizen.id}")

    print("\n--- POST-CHECK (WITHIN SAME SESSION) ---")
    log_count = db.query(AuditLog).count()
    print(f"Logs in same session: {log_count}")
    
    last_log = db.query(AuditLog).order_by(AuditLog.created_at.desc()).first()
    if last_log:
        print(f"Last Log Action: {last_log.action}")
        print(f"Last Log Resource: {last_log.resource_type}")

    print("\n--- PERSISTENCE TEST (NEW SESSION) ---")
    db.close()
    
    db2 = SessionLocal()
    log_count2 = db2.query(AuditLog).count()
    print(f"Logs in new session: {log_count2}")
    db2.close()

except Exception as e:
    print(f"ERROR: {e}")
    db.rollback()
finally:
    db.close()
