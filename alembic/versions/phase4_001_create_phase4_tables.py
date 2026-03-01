"""
NAYAM (नयम्) — Alembic Migration: Phase 4 Tables.

Creates the six Phase 4 tables:
  • sync_queue
  • conflict_logs
  • offline_actions
  • compliance_exports
  • performance_metrics
  • rate_limit_records

Revision ID: phase4_001
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "phase4_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── sync_queue ───────────────────────────────────────────────
    op.create_table(
        "sync_queue",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("node_id", sa.String(100), nullable=False),
        sa.Column("operation", sa.String(20), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sync_queue_node_id", "sync_queue", ["node_id"])
    op.create_index("ix_sync_queue_status", "sync_queue", ["status"])
    op.create_index("ix_sync_queue_resource", "sync_queue", ["resource_type", "resource_id"])
    op.create_index("ix_sync_queue_priority", "sync_queue", ["priority"])
    op.create_index("ix_sync_queue_created_at", "sync_queue", ["created_at"])

    # ── conflict_logs ────────────────────────────────────────────
    op.create_table(
        "conflict_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("sync_queue_id", sa.Uuid(), sa.ForeignKey("sync_queue.id", ondelete="SET NULL"), nullable=True),
        sa.Column("node_id", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("local_data", sa.JSON(), nullable=True),
        sa.Column("server_data", sa.JSON(), nullable=True),
        sa.Column("resolution", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("resolved_by", sa.Uuid(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_conflict_logs_sync_queue_id", "conflict_logs", ["sync_queue_id"])
    op.create_index("ix_conflict_logs_node_id", "conflict_logs", ["node_id"])
    op.create_index("ix_conflict_logs_resource", "conflict_logs", ["resource_type", "resource_id"])

    # ── offline_actions ──────────────────────────────────────────
    op.create_table(
        "offline_actions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("node_id", sa.String(100), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="cached"),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_offline_actions_node_id", "offline_actions", ["node_id"])
    op.create_index("ix_offline_actions_user_id", "offline_actions", ["user_id"])
    op.create_index("ix_offline_actions_status", "offline_actions", ["status"])
    op.create_index("ix_offline_actions_resource", "offline_actions", ["resource_type"])
    op.create_index("ix_offline_actions_created_at", "offline_actions", ["created_at"])

    # ── compliance_exports ───────────────────────────────────────
    op.create_table(
        "compliance_exports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("requested_by", sa.Uuid(), nullable=False),
        sa.Column("report_type", sa.String(100), nullable=False),
        sa.Column("export_format", sa.String(10), nullable=False, server_default="json"),
        sa.Column("status", sa.String(20), nullable=False, server_default="requested"),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("record_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_compliance_exports_requested_by", "compliance_exports", ["requested_by"])
    op.create_index("ix_compliance_exports_status", "compliance_exports", ["status"])

    # ── performance_metrics ──────────────────────────────────────
    op.create_table(
        "performance_metrics",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("endpoint", sa.String(500), nullable=True),
        sa.Column("method", sa.String(10), nullable=True),
        sa.Column("value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unit", sa.String(20), nullable=False, server_default="'ms'"),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("node_id", sa.String(100), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_performance_metrics_category", "performance_metrics", ["category"])
    op.create_index("ix_performance_metrics_endpoint", "performance_metrics", ["endpoint"])
    op.create_index("ix_performance_metrics_recorded_at", "performance_metrics", ["recorded_at"])

    # ── rate_limit_records ───────────────────────────────────────
    op.create_table(
        "rate_limit_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("client_ip", sa.String(45), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("endpoint", sa.String(500), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("window_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("blocked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_rate_limit_records_client_ip", "rate_limit_records", ["client_ip"])
    op.create_index("ix_rate_limit_records_endpoint", "rate_limit_records", ["endpoint"])
    op.create_index("ix_rate_limit_records_created_at", "rate_limit_records", ["created_at"])


def downgrade() -> None:
    op.drop_table("rate_limit_records")
    op.drop_table("performance_metrics")
    op.drop_table("compliance_exports")
    op.drop_table("offline_actions")
    op.drop_table("conflict_logs")
    op.drop_table("sync_queue")
