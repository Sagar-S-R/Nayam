from app.core.database import SessionLocal
from app.observability.models import AuditLog
from app.models.user import User as UserModel
from sqlalchemy import desc

db = SessionLocal()

query = db.query(AuditLog).order_by(desc(AuditLog.created_at))
total = query.count()
entries = query.all()

print(f"Total entries found: {total}")

result = []
for e in entries:
    actor_name = "System"
    actor_role = "system"
    if e.user_id:
        user = db.query(UserModel).filter(UserModel.id == e.user_id).first()
        if user:
            actor_name = user.full_name or user.email
            actor_role = user.role.value

    result.append({
        "id": str(e.id),
        "timestamp": e.created_at.isoformat(),
        "actor_name": actor_name,
        "actor_role": actor_role,
        "action": e.action.value if hasattr(e.action, "value") else str(e.action),
        "resource_type": e.resource_type,
        "resource_id": e.resource_id,
        "description": e.description or "",
    })

for r in result:
    print(r)

db.close()
