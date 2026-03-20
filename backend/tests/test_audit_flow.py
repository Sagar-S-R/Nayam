from app.core.database import SessionLocal
from app.services.citizen import CitizenService
from app.schemas.citizen import CitizenCreateRequest
from app.observability.models import AuditLog
from sqlalchemy import desc

db = SessionLocal()
service = CitizenService(db)

# Create a test citizen
payload = CitizenCreateRequest(
    name="Audit Test Citizen",
    contact_number="9998887776",
    ward="Ward-1"
)

print("Creating test citizen...")
citizen = service.create_citizen(payload)
print(f"Citizen created: {citizen.id}")

# Check audit log
print("Checking audit log...")
latest_log = db.query(AuditLog).order_by(desc(AuditLog.created_at)).first()

if latest_log and latest_log.resource_id == str(citizen.id):
    print("SUCCESS: Audit log entry found!")
    print(f"Action: {latest_log.action}")
    print(f"Resource: {latest_log.resource_type}")
    print(f"Description: {latest_log.description}")
else:
    print("FAILURE: Audit log entry not found or mismatch.")
    if latest_log:
        print(f"Latest log was for resource: {latest_log.resource_id}")

db.close()
