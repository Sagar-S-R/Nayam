#!/usr/bin/env python3
"""
Seed compliance_exports table with sample data.

This populates the ComplianceExport table so the compliance page
has audit data to display alongside action requests.
"""

import sqlite3
from datetime import datetime, timedelta, timezone
import uuid
import json

DB_PATH = "/Users/samrudhp/Projects-git/Nayam/nayam_dev.db"

# Sample compliance export records
COMPLIANCE_EXPORTS = [
    {
        "id": str(uuid.uuid4()),
        "requested_by": "leader-001",  # User UUID (we'll use this as placeholder)
        "report_type": "audit_summary",
        "export_format": "PDF",
        "status": "completed",
        "parameters": json.dumps({"date_range": "last_7_days", "ward": "all"}),
        "record_count": 42,
        "file_path": "/exports/NAYAM_AuditTrail_20260315_140530.pdf",
        "file_size_bytes": 245632,
        "error_message": None,
        "requested_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        "completed_at": (datetime.now(timezone.utc) - timedelta(days=5, hours=1)).isoformat(),
    },
    {
        "id": str(uuid.uuid4()),
        "requested_by": "analyst-001",
        "report_type": "access_log",
        "export_format": "CSV",
        "status": "completed",
        "parameters": json.dumps({"date_range": "last_30_days"}),
        "record_count": 156,
        "file_path": "/exports/access_log_20260310.csv",
        "file_size_bytes": 89234,
        "error_message": None,
        "requested_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
        "completed_at": (datetime.now(timezone.utc) - timedelta(days=10, hours=2)).isoformat(),
    },
    {
        "id": str(uuid.uuid4()),
        "requested_by": "leader-001",
        "report_type": "full_dump",
        "export_format": "JSON",
        "status": "completed",
        "parameters": json.dumps({"include_archived": False}),
        "record_count": 523,
        "file_path": "/exports/full_dump_20260312_093015.json",
        "file_size_bytes": 1024532,
        "error_message": None,
        "requested_at": (datetime.now(timezone.utc) - timedelta(days=8)).isoformat(),
        "completed_at": (datetime.now(timezone.utc) - timedelta(days=8, hours=3)).isoformat(),
    },
    {
        "id": str(uuid.uuid4()),
        "requested_by": "analyst-002",
        "report_type": "compliance_check",
        "export_format": "PDF",
        "status": "completed",
        "parameters": json.dumps({"department": "core"}),
        "record_count": 78,
        "file_path": "/exports/compliance_report_20260314.pdf",
        "file_size_bytes": 312456,
        "error_message": None,
        "requested_at": (datetime.now(timezone.utc) - timedelta(days=6)).isoformat(),
        "completed_at": (datetime.now(timezone.utc) - timedelta(days=6, hours=1, minutes=30)).isoformat(),
    },
    {
        "id": str(uuid.uuid4()),
        "requested_by": "leader-001",
        "report_type": "audit_summary",
        "export_format": "CSV",
        "status": "processing",
        "parameters": json.dumps({"date_range": "last_2_days"}),
        "record_count": None,
        "file_path": None,
        "file_size_bytes": None,
        "error_message": None,
        "requested_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        "completed_at": None,
    },
]

def seed_compliance_exports():
    """Insert sample compliance export records."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check existing count
        cursor.execute("SELECT COUNT(*) FROM compliance_exports")
        existing = cursor.fetchone()[0]
        
        if existing > 0:
            print(f"⚠️  Table already has {existing} records. Skipping insert.")
            conn.close()
            return
        
        # Insert sample records
        for export in COMPLIANCE_EXPORTS:
            cursor.execute("""
                INSERT INTO compliance_exports 
                (id, requested_by, report_type, export_format, status, parameters, 
                 record_count, file_path, file_size_bytes, error_message, requested_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                export["id"],
                export["requested_by"],
                export["report_type"],
                export["export_format"],
                export["status"],
                export["parameters"],
                export["record_count"],
                export["file_path"],
                export["file_size_bytes"],
                export["error_message"],
                export["requested_at"],
                export["completed_at"],
            ))
        
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM compliance_exports")
        total = cursor.fetchone()[0]
        print(f"✅ Seeded {total} compliance export records")
        conn.close()
        
    except Exception as e:
        print(f"❌ Error seeding compliance exports: {e}")
        raise

if __name__ == "__main__":
    seed_compliance_exports()
