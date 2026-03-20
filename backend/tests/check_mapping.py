from app.core.database import SessionLocal, Base
from app.observability.models import AuditLog
from sqlalchemy import inspect

db = SessionLocal()
engine = db.get_bind()
inspector = inspect(engine)

print("--- DB INSPECTION ---")
print(f"Engine: {engine}")
print(f"Tables found: {inspector.get_table_names()}")

if "audit_logs" in inspector.get_table_names():
    print("Columns in 'audit_logs':")
    for col in inspector.get_columns("audit_logs"):
        print(f" - {col['name']} ({col['type']})")
else:
    print("CRITICAL: 'audit_logs' table MISSSING in SQLAlchemy engine's context!")

# Check if AuditLog is mapped correctly
print("\n--- MAPPING CHECK ---")
mapper = inspect(AuditLog)
print(f"Mapped table: {mapper.local_table.name}")
for attr in mapper.column_attrs:
    print(f" - Attr: {attr.key} -> Col: {attr.columns[0].name}")

db.close()
