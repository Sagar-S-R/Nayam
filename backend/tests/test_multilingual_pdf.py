#!/usr/bin/env python
"""Test multilingual PDF generation."""

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.compliance.audit_trail_pdf import generate_audit_trail_pdf
from app.models.action_request import ActionRequest
from datetime import datetime

# Get some audit entries
db = SessionLocal()
entries = db.query(ActionRequest).order_by(ActionRequest.created_at.desc()).limit(10).all()
print(f"Found {len(entries)} audit entries")

# Get a user to test with
user = db.query(User).first()
if not user:
    # Create a test user
    user = User(
        name="Test User",
        email="test@gov.in",
        role=UserRole.LEADER,
        password_hash="test",
    )
    db.add(user)
    db.commit()
    print("Created test user")
else:
    print(f"Using user: {user.name} ({user.role.value})")

# Generate PDF with hindi
print("\n--- Testing with Hindi support ---")
pdf_bytes = generate_audit_trail_pdf(entries, user, include_hindi=True)
print(f"PDF generated with Hindi: {len(pdf_bytes)} bytes")

# Save to disk for inspection
with open("/tmp/test_audit_hindi.pdf", "wb") as f:
    f.write(pdf_bytes)
print("Saved to /tmp/test_audit_hindi.pdf")

# Generate PDF without hindi
print("\n--- Testing without Hindi support ---")
pdf_bytes = generate_audit_trail_pdf(entries, user, include_hindi=False)
print(f"PDF generated without Hindi: {len(pdf_bytes)} bytes")

# Save to disk for inspection
with open("/tmp/test_audit_english.pdf", "wb") as f:
    f.write(pdf_bytes)
print("Saved to /tmp/test_audit_english.pdf")

db.close()
print("\nTest completed successfully!")
