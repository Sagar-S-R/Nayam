"""
NAYAM (नयम्) — Phase 4 Step 2 Tests.

Covers: Repositories, Services, and Rate-Limiter Middleware for all
five Phase 4 modules (sync, offline, hardening, compliance, monitoring).

Target: 80+ tests across the six repository classes, five service
classes, and the RateLimitMiddleware.
"""

import json
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base

# ── Models ────────────────────────────────────────────────────────────
from app.sync.models import SyncQueue, SyncStatus, SyncOperation
from app.sync.conflict_model import ConflictLog, ConflictResolution
from app.offline.models import OfflineAction, OfflineStatus
from app.compliance.models import ComplianceExport, ExportFormat, ExportStatus
from app.monitoring.models import PerformanceMetric, MetricCategory
from app.hardening.models import RateLimitRecord

# ── Repositories ──────────────────────────────────────────────────────
from app.sync.repository import SyncQueueRepository
from app.sync.conflict_repository import ConflictLogRepository
from app.offline.repository import OfflineActionRepository
from app.compliance.repository import ComplianceExportRepository
from app.monitoring.repository import PerformanceMetricRepository
from app.hardening.repository import RateLimitRepository

# ── Services ──────────────────────────────────────────────────────────
from app.sync.service import SyncService
from app.offline.service import OfflineService
from app.compliance.service import ComplianceService
from app.monitoring.service import MonitoringService

# ── Middleware ─────────────────────────────────────────────────────────
from app.hardening.rate_limiter import (
    RateLimitMiddleware,
    _is_rate_limited,
    reset_rate_limiter,
)

# ── Test DB Setup ─────────────────────────────────────────────────────
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _setup_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db() -> Session:
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


# ── Helpers ───────────────────────────────────────────────────────────

def _make_sync_entry(db: Session, **overrides) -> SyncQueue:
    defaults = dict(
        node_id="edge-1",
        operation=SyncOperation.CREATE,
        resource_type="issue",
        resource_id=uuid.uuid4(),
        payload={"title": "test"},
        version=1,
        priority=5,
        checksum="abc123",
    )
    defaults.update(overrides)
    entry = SyncQueue(**defaults)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def _make_conflict(db: Session, sync_entry: SyncQueue, **overrides) -> ConflictLog:
    defaults = dict(
        sync_queue_id=sync_entry.id,
        node_id=sync_entry.node_id,
        resource_type=sync_entry.resource_type,
        resource_id=sync_entry.resource_id,
        local_data={"title": "local"},
        server_data={"title": "server"},
    )
    defaults.update(overrides)
    conflict = ConflictLog(**defaults)
    db.add(conflict)
    db.commit()
    db.refresh(conflict)
    return conflict


def _make_offline_action(db: Session, **overrides) -> OfflineAction:
    defaults = dict(
        node_id="edge-1",
        user_id=uuid.uuid4(),
        action_type="create_issue",
        resource_type="issue",
        resource_id=uuid.uuid4(),
        payload={"title": "offline"},
        checksum="def456",
    )
    defaults.update(overrides)
    action = OfflineAction(**defaults)
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def _make_compliance_export(db: Session, **overrides) -> ComplianceExport:
    defaults = dict(
        requested_by=uuid.uuid4(),
        report_type="audit_summary",
        export_format=ExportFormat.JSON,
    )
    defaults.update(overrides)
    export = ComplianceExport(**defaults)
    db.add(export)
    db.commit()
    db.refresh(export)
    return export


def _make_metric(db: Session, **overrides) -> PerformanceMetric:
    defaults = dict(
        category=MetricCategory.API_LATENCY,
        endpoint="/api/v1/issues",
        method="GET",
        value=42.5,
        unit="ms",
        status_code=200,
    )
    defaults.update(overrides)
    metric = PerformanceMetric(**defaults)
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def _make_rate_record(db: Session, **overrides) -> RateLimitRecord:
    defaults = dict(
        client_ip="192.168.1.1",
        endpoint="/api/v1/issues",
        window_seconds=60,
        blocked=0,
    )
    defaults.update(overrides)
    rec = RateLimitRecord(**defaults)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


# =====================================================================
#  1. SyncQueueRepository Tests
# =====================================================================

class TestSyncQueueRepository:

    def test_create_and_get(self, db):
        repo = SyncQueueRepository(db)
        entry = SyncQueue(
            node_id="edge-1", operation=SyncOperation.CREATE,
            resource_type="citizen", resource_id=uuid.uuid4(),
            payload={"name": "x"}, version=1, checksum="aaa",
        )
        created = repo.create(entry)
        assert created.id is not None
        fetched = repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.node_id == "edge-1"

    def test_get_by_id_not_found(self, db):
        repo = SyncQueueRepository(db)
        assert repo.get_by_id(uuid.uuid4()) is None

    def test_mark_in_progress(self, db):
        entry = _make_sync_entry(db)
        repo = SyncQueueRepository(db)
        updated = repo.mark_in_progress(entry)
        assert updated.status == SyncStatus.IN_PROGRESS

    def test_mark_synced(self, db):
        entry = _make_sync_entry(db, status=SyncStatus.IN_PROGRESS)
        repo = SyncQueueRepository(db)
        updated = repo.mark_synced(entry)
        assert updated.status == SyncStatus.SYNCED
        assert updated.synced_at is not None

    def test_mark_failed_increments_retry(self, db):
        entry = _make_sync_entry(db, status=SyncStatus.IN_PROGRESS)
        repo = SyncQueueRepository(db)
        updated = repo.mark_failed(entry, "timeout")
        assert updated.status == SyncStatus.FAILED
        assert updated.retry_count == 1
        assert updated.error_message == "timeout"

    def test_mark_conflict(self, db):
        entry = _make_sync_entry(db)
        repo = SyncQueueRepository(db)
        updated = repo.mark_conflict(entry)
        assert updated.status == SyncStatus.CONFLICT

    def test_get_pending(self, db):
        _make_sync_entry(db, node_id="a")
        _make_sync_entry(db, node_id="b")
        _make_sync_entry(db, node_id="a", status=SyncStatus.SYNCED)
        repo = SyncQueueRepository(db)
        items, total = repo.get_pending()
        assert total == 2
        assert len(items) == 2

    def test_get_pending_by_node(self, db):
        _make_sync_entry(db, node_id="a")
        _make_sync_entry(db, node_id="b")
        repo = SyncQueueRepository(db)
        items, total = repo.get_pending(node_id="a")
        assert total == 1

    def test_get_retryable(self, db):
        _make_sync_entry(db, status=SyncStatus.FAILED, retry_count=1)
        _make_sync_entry(db, status=SyncStatus.FAILED, retry_count=5)
        repo = SyncQueueRepository(db)
        retryable = repo.get_retryable(max_retries=3)
        assert len(retryable) == 1

    def test_get_by_node(self, db):
        _make_sync_entry(db, node_id="x")
        _make_sync_entry(db, node_id="x")
        _make_sync_entry(db, node_id="y")
        repo = SyncQueueRepository(db)
        items, total = repo.get_by_node("x")
        assert total == 2

    def test_get_by_resource(self, db):
        rid = uuid.uuid4()
        _make_sync_entry(db, resource_type="issue", resource_id=rid, version=1)
        _make_sync_entry(db, resource_type="issue", resource_id=rid, version=2)
        repo = SyncQueueRepository(db)
        items = repo.get_by_resource("issue", rid)
        assert len(items) == 2
        assert items[0].version >= items[1].version

    def test_count_by_status(self, db):
        _make_sync_entry(db)
        _make_sync_entry(db, status=SyncStatus.SYNCED)
        repo = SyncQueueRepository(db)
        counts = repo.count_by_status()
        assert len(counts) >= 1

    def test_delete(self, db):
        entry = _make_sync_entry(db)
        repo = SyncQueueRepository(db)
        repo.delete(entry)
        assert repo.get_by_id(entry.id) is None


# =====================================================================
#  2. ConflictLogRepository Tests
# =====================================================================

class TestConflictLogRepository:

    def test_create_and_get(self, db):
        sync_entry = _make_sync_entry(db)
        repo = ConflictLogRepository(db)
        conflict = ConflictLog(
            sync_queue_id=sync_entry.id, node_id="edge-1",
            resource_type="issue", resource_id=uuid.uuid4(),
            local_data={"a": 1}, server_data={"a": 2},
        )
        created = repo.create(conflict)
        assert created.id is not None
        assert repo.get_by_id(created.id) is not None

    def test_resolve(self, db):
        sync_entry = _make_sync_entry(db)
        conflict = _make_conflict(db, sync_entry)
        repo = ConflictLogRepository(db)
        user_id = uuid.uuid4()
        resolved = repo.resolve(conflict, ConflictResolution.LOCAL_WINS, user_id, "keep local")
        assert resolved.resolution == ConflictResolution.LOCAL_WINS
        assert resolved.resolved_by == user_id
        assert resolved.resolved_at is not None

    def test_get_pending(self, db):
        se = _make_sync_entry(db)
        _make_conflict(db, se)
        _make_conflict(db, se)
        repo = ConflictLogRepository(db)
        items, total = repo.get_pending()
        assert total == 2

    def test_get_by_node(self, db):
        se = _make_sync_entry(db, node_id="n1")
        _make_conflict(db, se, node_id="n1")
        repo = ConflictLogRepository(db)
        items = repo.get_by_node("n1")
        assert len(items) == 1

    def test_get_by_sync_entry(self, db):
        se = _make_sync_entry(db)
        _make_conflict(db, se)
        repo = ConflictLogRepository(db)
        found = repo.get_by_sync_entry(se.id)
        assert found is not None

    def test_pending_count(self, db):
        se = _make_sync_entry(db)
        _make_conflict(db, se)
        repo = ConflictLogRepository(db)
        assert repo.pending_count() == 1

    def test_delete(self, db):
        se = _make_sync_entry(db)
        conflict = _make_conflict(db, se)
        repo = ConflictLogRepository(db)
        repo.delete(conflict)
        assert repo.get_by_id(conflict.id) is None


# =====================================================================
#  3. OfflineActionRepository Tests
# =====================================================================

class TestOfflineActionRepository:

    def test_create_and_get(self, db):
        repo = OfflineActionRepository(db)
        action = OfflineAction(
            node_id="edge-1", user_id=uuid.uuid4(),
            action_type="create_issue", resource_type="issue",
            resource_id=uuid.uuid4(), payload={"x": 1}, checksum="aaa",
        )
        created = repo.create(action)
        assert created.id is not None
        assert repo.get_by_id(created.id) is not None

    def test_mark_queued(self, db):
        action = _make_offline_action(db)
        repo = OfflineActionRepository(db)
        updated = repo.mark_queued(action)
        assert updated.status == OfflineStatus.QUEUED
        assert updated.queued_at is not None

    def test_mark_synced(self, db):
        action = _make_offline_action(db)
        repo = OfflineActionRepository(db)
        updated = repo.mark_synced(action)
        assert updated.status == OfflineStatus.SYNCED

    def test_mark_failed(self, db):
        action = _make_offline_action(db)
        repo = OfflineActionRepository(db)
        updated = repo.mark_failed(action)
        assert updated.status == OfflineStatus.FAILED

    def test_get_cached(self, db):
        _make_offline_action(db, node_id="a")
        _make_offline_action(db, node_id="b")
        _make_offline_action(db, node_id="a", status=OfflineStatus.SYNCED)
        repo = OfflineActionRepository(db)
        items, total = repo.get_cached()
        assert total == 2

    def test_get_cached_by_node(self, db):
        _make_offline_action(db, node_id="a")
        _make_offline_action(db, node_id="b")
        repo = OfflineActionRepository(db)
        items, total = repo.get_cached(node_id="a")
        assert total == 1

    def test_get_by_node(self, db):
        _make_offline_action(db, node_id="x")
        _make_offline_action(db, node_id="x")
        repo = OfflineActionRepository(db)
        items, total = repo.get_by_node("x")
        assert total == 2

    def test_get_by_user(self, db):
        uid = uuid.uuid4()
        _make_offline_action(db, user_id=uid)
        _make_offline_action(db, user_id=uid)
        repo = OfflineActionRepository(db)
        items = repo.get_by_user(uid)
        assert len(items) == 2

    def test_count_by_status(self, db):
        _make_offline_action(db)
        _make_offline_action(db, status=OfflineStatus.SYNCED)
        repo = OfflineActionRepository(db)
        counts = repo.count_by_status()
        assert len(counts) >= 1

    def test_delete(self, db):
        action = _make_offline_action(db)
        repo = OfflineActionRepository(db)
        repo.delete(action)
        assert repo.get_by_id(action.id) is None


# =====================================================================
#  4. ComplianceExportRepository Tests
# =====================================================================

class TestComplianceExportRepository:

    def test_create_and_get(self, db):
        repo = ComplianceExportRepository(db)
        export = ComplianceExport(
            requested_by=uuid.uuid4(), report_type="audit", export_format=ExportFormat.CSV,
        )
        created = repo.create(export)
        assert created.id is not None
        assert repo.get_by_id(created.id) is not None

    def test_mark_processing(self, db):
        export = _make_compliance_export(db)
        repo = ComplianceExportRepository(db)
        updated = repo.mark_processing(export)
        assert updated.status == ExportStatus.PROCESSING

    def test_mark_completed(self, db):
        export = _make_compliance_export(db, status=ExportStatus.PROCESSING)
        repo = ComplianceExportRepository(db)
        updated = repo.mark_completed(export, "/exports/f.json", 1024, 50)
        assert updated.status == ExportStatus.COMPLETED
        assert updated.file_path == "/exports/f.json"
        assert updated.file_size_bytes == 1024
        assert updated.record_count == 50
        assert updated.completed_at is not None

    def test_mark_failed(self, db):
        export = _make_compliance_export(db)
        repo = ComplianceExportRepository(db)
        updated = repo.mark_failed(export, "disk full")
        assert updated.status == ExportStatus.FAILED
        assert updated.error_message == "disk full"

    def test_get_by_user(self, db):
        uid = uuid.uuid4()
        _make_compliance_export(db, requested_by=uid)
        _make_compliance_export(db, requested_by=uid)
        repo = ComplianceExportRepository(db)
        items, total = repo.get_by_user(uid)
        assert total == 2

    def test_get_all(self, db):
        _make_compliance_export(db)
        _make_compliance_export(db, status=ExportStatus.COMPLETED)
        repo = ComplianceExportRepository(db)
        items, total = repo.get_all()
        assert total == 2

    def test_get_all_filtered(self, db):
        _make_compliance_export(db)
        _make_compliance_export(db, status=ExportStatus.COMPLETED)
        repo = ComplianceExportRepository(db)
        items, total = repo.get_all(status_filter=ExportStatus.COMPLETED)
        assert total == 1

    def test_delete(self, db):
        export = _make_compliance_export(db)
        repo = ComplianceExportRepository(db)
        repo.delete(export)
        assert repo.get_by_id(export.id) is None


# =====================================================================
#  5. PerformanceMetricRepository Tests
# =====================================================================

class TestPerformanceMetricRepository:

    def test_create_and_get(self, db):
        repo = PerformanceMetricRepository(db)
        metric = PerformanceMetric(
            category=MetricCategory.API_LATENCY, value=12.3, unit="ms",
        )
        created = repo.create(metric)
        assert created.id is not None
        assert repo.get_by_id(created.id) is not None

    def test_create_batch(self, db):
        repo = PerformanceMetricRepository(db)
        metrics = [
            PerformanceMetric(category=MetricCategory.API_LATENCY, value=10.0, unit="ms"),
            PerformanceMetric(category=MetricCategory.DB_QUERY, value=5.0, unit="ms"),
        ]
        created = repo.create_batch(metrics)
        assert len(created) == 2
        assert repo.total_count() == 2

    def test_get_by_category(self, db):
        _make_metric(db, category=MetricCategory.API_LATENCY)
        _make_metric(db, category=MetricCategory.DB_QUERY)
        repo = PerformanceMetricRepository(db)
        items, total = repo.get_by_category(MetricCategory.API_LATENCY)
        assert total == 1

    def test_get_by_endpoint(self, db):
        _make_metric(db, endpoint="/api/v1/issues")
        _make_metric(db, endpoint="/api/v1/citizens")
        repo = PerformanceMetricRepository(db)
        items = repo.get_by_endpoint("/api/v1/issues")
        assert len(items) == 1

    def test_get_recent(self, db):
        _make_metric(db)
        _make_metric(db)
        repo = PerformanceMetricRepository(db)
        items = repo.get_recent(limit=10)
        assert len(items) == 2

    def test_average_by_category(self, db):
        _make_metric(db, category=MetricCategory.API_LATENCY, value=10.0)
        _make_metric(db, category=MetricCategory.API_LATENCY, value=20.0)
        repo = PerformanceMetricRepository(db)
        avg = repo.average_by_category(MetricCategory.API_LATENCY)
        assert avg == pytest.approx(15.0)

    def test_average_empty(self, db):
        repo = PerformanceMetricRepository(db)
        assert repo.average_by_category(MetricCategory.CPU_USAGE) is None

    def test_total_count(self, db):
        _make_metric(db)
        repo = PerformanceMetricRepository(db)
        assert repo.total_count() == 1

    def test_delete(self, db):
        metric = _make_metric(db)
        repo = PerformanceMetricRepository(db)
        repo.delete(metric)
        assert repo.get_by_id(metric.id) is None


# =====================================================================
#  6. RateLimitRepository Tests
# =====================================================================

class TestRateLimitRepository:

    def test_create_and_get(self, db):
        repo = RateLimitRepository(db)
        rec = RateLimitRecord(
            client_ip="10.0.0.1", endpoint="/test", window_seconds=60,
        )
        created = repo.create(rec)
        assert created.id is not None
        assert repo.get_by_id(created.id) is not None

    def test_get_by_ip(self, db):
        _make_rate_record(db, client_ip="1.1.1.1")
        _make_rate_record(db, client_ip="2.2.2.2")
        repo = RateLimitRepository(db)
        items, total = repo.get_by_ip("1.1.1.1")
        assert total == 1

    def test_get_blocked(self, db):
        _make_rate_record(db, blocked=0)
        _make_rate_record(db, blocked=1)
        _make_rate_record(db, blocked=1)
        repo = RateLimitRepository(db)
        items, total = repo.get_blocked()
        assert total == 2

    def test_count_by_ip(self, db):
        _make_rate_record(db, client_ip="3.3.3.3")
        _make_rate_record(db, client_ip="3.3.3.3")
        repo = RateLimitRepository(db)
        since = datetime(2000, 1, 1, tzinfo=timezone.utc)
        assert repo.count_by_ip("3.3.3.3", since) == 2

    def test_count_blocked(self, db):
        _make_rate_record(db, blocked=1)
        repo = RateLimitRepository(db)
        assert repo.count_blocked() == 1

    def test_total_count(self, db):
        _make_rate_record(db)
        _make_rate_record(db)
        repo = RateLimitRepository(db)
        assert repo.total_count() == 2

    def test_get_top_offenders(self, db):
        _make_rate_record(db, client_ip="bad", blocked=1)
        _make_rate_record(db, client_ip="bad", blocked=1)
        _make_rate_record(db, client_ip="ok", blocked=1)
        repo = RateLimitRepository(db)
        top = repo.get_top_offenders(limit=5)
        assert len(top) == 2
        assert top[0][0] == "bad"
        assert top[0][1] == 2

    def test_delete(self, db):
        rec = _make_rate_record(db)
        repo = RateLimitRepository(db)
        repo.delete(rec)
        assert repo.get_by_id(rec.id) is None


# =====================================================================
#  7. SyncService Tests
# =====================================================================

class TestSyncService:

    def test_enqueue(self, db):
        svc = SyncService(db)
        entry = svc.enqueue(
            node_id="edge-1", operation=SyncOperation.CREATE,
            resource_type="issue", resource_id=uuid.uuid4(),
            payload={"title": "x"}, priority=3,
        )
        assert entry.status == SyncStatus.PENDING
        assert entry.version == 1
        assert entry.checksum is not None

    def test_enqueue_increments_version(self, db):
        svc = SyncService(db)
        rid = uuid.uuid4()
        e1 = svc.enqueue("edge-1", SyncOperation.CREATE, "issue", rid, {"v": 1})
        e2 = svc.enqueue("edge-1", SyncOperation.UPDATE, "issue", rid, {"v": 2})
        assert e2.version == e1.version + 1

    def test_get_entry_not_found(self, db):
        svc = SyncService(db)
        with pytest.raises(Exception) as exc_info:
            svc.get_entry(uuid.uuid4())
        assert exc_info.value.status_code == 404

    def test_begin_sync(self, db):
        svc = SyncService(db)
        entry = svc.enqueue("e", SyncOperation.CREATE, "issue", uuid.uuid4())
        progressed = svc.begin_sync(entry.id)
        assert progressed.status == SyncStatus.IN_PROGRESS

    def test_begin_sync_wrong_status(self, db):
        entry = _make_sync_entry(db, status=SyncStatus.SYNCED)
        svc = SyncService(db)
        with pytest.raises(Exception) as exc_info:
            svc.begin_sync(entry.id)
        assert exc_info.value.status_code == 409

    def test_complete_sync(self, db):
        entry = _make_sync_entry(db, status=SyncStatus.IN_PROGRESS)
        svc = SyncService(db)
        done = svc.complete_sync(entry.id)
        assert done.status == SyncStatus.SYNCED

    def test_fail_sync(self, db):
        entry = _make_sync_entry(db, status=SyncStatus.IN_PROGRESS)
        svc = SyncService(db)
        failed = svc.fail_sync(entry.id, "network error")
        assert failed.status == SyncStatus.FAILED
        assert failed.error_message == "network error"

    def test_retry_failed(self, db):
        _make_sync_entry(db, status=SyncStatus.FAILED, retry_count=1)
        _make_sync_entry(db, status=SyncStatus.FAILED, retry_count=10)
        svc = SyncService(db)
        reset = svc.retry_failed()
        assert len(reset) == 1
        assert reset[0].status == SyncStatus.PENDING

    def test_list_pending(self, db):
        svc = SyncService(db)
        svc.enqueue("e", SyncOperation.CREATE, "issue", uuid.uuid4())
        items, total = svc.list_pending()
        assert total == 1

    def test_status_summary(self, db):
        _make_sync_entry(db)
        _make_sync_entry(db, status=SyncStatus.SYNCED)
        svc = SyncService(db)
        summary = svc.status_summary()
        assert "pending" in summary
        assert "synced" in summary

    def test_raise_conflict(self, db):
        svc = SyncService(db)
        entry = svc.enqueue("e", SyncOperation.UPDATE, "issue", uuid.uuid4(), {"a": 1})
        conflict = svc.raise_conflict(entry.id, {"a": 1}, {"a": 2})
        assert conflict.resolution == ConflictResolution.PENDING
        # Sync entry should now be CONFLICT
        refreshed = svc.get_entry(entry.id)
        assert refreshed.status == SyncStatus.CONFLICT

    def test_resolve_conflict(self, db):
        se = _make_sync_entry(db)
        conflict = _make_conflict(db, se)
        svc = SyncService(db)
        resolved = svc.resolve_conflict(conflict.id, ConflictResolution.SERVER_WINS, notes="auto")
        assert resolved.resolution == ConflictResolution.SERVER_WINS

    def test_resolve_conflict_not_found(self, db):
        svc = SyncService(db)
        with pytest.raises(Exception) as exc_info:
            svc.resolve_conflict(uuid.uuid4(), ConflictResolution.LOCAL_WINS)
        assert exc_info.value.status_code == 404

    def test_resolve_already_resolved(self, db):
        se = _make_sync_entry(db)
        conflict = _make_conflict(db, se)
        repo = ConflictLogRepository(db)
        repo.resolve(conflict, ConflictResolution.MERGED)
        svc = SyncService(db)
        with pytest.raises(Exception) as exc_info:
            svc.resolve_conflict(conflict.id, ConflictResolution.LOCAL_WINS)
        assert exc_info.value.status_code == 409

    def test_verify_checksum_valid(self, db):
        svc = SyncService(db)
        payload = {"key": "value"}
        entry = svc.enqueue("e", SyncOperation.CREATE, "issue", uuid.uuid4(), payload)
        assert svc.verify_checksum(entry.id) is True

    def test_compute_checksum_deterministic(self):
        a = SyncService.compute_checksum({"b": 2, "a": 1})
        b = SyncService.compute_checksum({"a": 1, "b": 2})
        assert a == b

    def test_pending_conflict_count(self, db):
        se = _make_sync_entry(db)
        _make_conflict(db, se)
        svc = SyncService(db)
        assert svc.pending_conflict_count() == 1


# =====================================================================
#  8. OfflineService Tests
# =====================================================================

class TestOfflineService:

    def test_cache_action(self, db):
        svc = OfflineService(db)
        action = svc.cache_action(
            node_id="edge-1", user_id=uuid.uuid4(),
            action_type="create_issue", resource_type="issue",
            payload={"title": "test"},
        )
        assert action.status == OfflineStatus.CACHED
        assert action.checksum is not None

    def test_get_action_not_found(self, db):
        svc = OfflineService(db)
        with pytest.raises(Exception) as exc_info:
            svc.get_action(uuid.uuid4())
        assert exc_info.value.status_code == 404

    def test_promote_to_queue(self, db):
        svc = OfflineService(db)
        action = svc.cache_action("e", uuid.uuid4(), "create_issue", "issue", payload={"a": 1})
        promoted = svc.promote_to_queue(action.id)
        assert promoted.status == OfflineStatus.QUEUED
        assert promoted.queued_at is not None
        # Verify a sync-queue entry was created
        sync_items, _ = svc.sync_service.list_pending()
        assert len(sync_items) == 1

    def test_promote_wrong_status(self, db):
        action = _make_offline_action(db, status=OfflineStatus.QUEUED)
        svc = OfflineService(db)
        with pytest.raises(Exception) as exc_info:
            svc.promote_to_queue(action.id)
        assert exc_info.value.status_code == 409

    def test_promote_all_cached(self, db):
        svc = OfflineService(db)
        svc.cache_action("e", uuid.uuid4(), "create_issue", "issue", payload={"a": 1})
        svc.cache_action("e", uuid.uuid4(), "update_citizen", "citizen", payload={"b": 2})
        count = svc.promote_all_cached()
        assert count == 2

    def test_list_cached(self, db):
        svc = OfflineService(db)
        svc.cache_action("e", uuid.uuid4(), "create_issue", "issue")
        items, total = svc.list_cached()
        assert total == 1

    def test_list_by_user(self, db):
        uid = uuid.uuid4()
        svc = OfflineService(db)
        svc.cache_action("e", uid, "create_issue", "issue")
        items = svc.list_by_user(uid)
        assert len(items) == 1

    def test_status_summary(self, db):
        _make_offline_action(db)
        _make_offline_action(db, status=OfflineStatus.SYNCED)
        svc = OfflineService(db)
        summary = svc.status_summary()
        assert "cached" in summary
        assert "synced" in summary

    def test_map_action_create(self, db):
        svc = OfflineService(db)
        assert svc._map_action_to_operation("create_issue") == SyncOperation.CREATE

    def test_map_action_delete(self, db):
        svc = OfflineService(db)
        assert svc._map_action_to_operation("delete_citizen") == SyncOperation.DELETE

    def test_map_action_update(self, db):
        svc = OfflineService(db)
        assert svc._map_action_to_operation("edit_issue") == SyncOperation.UPDATE

    def test_verify_checksum(self, db):
        svc = OfflineService(db)
        action = svc.cache_action("e", uuid.uuid4(), "create_issue", "issue", payload={"x": 1})
        assert svc.verify_checksum(action.id) is True

    def test_mark_synced(self, db):
        action = _make_offline_action(db)
        svc = OfflineService(db)
        updated = svc.mark_synced(action.id)
        assert updated.status == OfflineStatus.SYNCED

    def test_mark_failed(self, db):
        action = _make_offline_action(db)
        svc = OfflineService(db)
        updated = svc.mark_failed(action.id)
        assert updated.status == OfflineStatus.FAILED


# =====================================================================
#  9. ComplianceService Tests
# =====================================================================

class TestComplianceService:

    def test_request_export(self, db):
        svc = ComplianceService(db)
        export = svc.request_export(uuid.uuid4(), "audit_summary", ExportFormat.CSV, {"ward": "A"})
        assert export.status == ExportStatus.REQUESTED
        assert export.export_format == ExportFormat.CSV

    def test_get_export_not_found(self, db):
        svc = ComplianceService(db)
        with pytest.raises(Exception) as exc_info:
            svc.get_export(uuid.uuid4())
        assert exc_info.value.status_code == 404

    def test_begin_processing(self, db):
        svc = ComplianceService(db)
        export = svc.request_export(uuid.uuid4(), "audit")
        updated = svc.begin_processing(export.id)
        assert updated.status == ExportStatus.PROCESSING

    def test_begin_processing_wrong_status(self, db):
        export = _make_compliance_export(db, status=ExportStatus.COMPLETED)
        svc = ComplianceService(db)
        with pytest.raises(Exception) as exc_info:
            svc.begin_processing(export.id)
        assert exc_info.value.status_code == 409

    def test_complete_export(self, db):
        export = _make_compliance_export(db, status=ExportStatus.PROCESSING)
        svc = ComplianceService(db)
        done = svc.complete_export(export.id, "/exports/x.json", 2048, 100)
        assert done.status == ExportStatus.COMPLETED
        assert done.record_count == 100

    def test_fail_export(self, db):
        export = _make_compliance_export(db)
        svc = ComplianceService(db)
        failed = svc.fail_export(export.id, "io error")
        assert failed.status == ExportStatus.FAILED

    def test_list_by_user(self, db):
        uid = uuid.uuid4()
        svc = ComplianceService(db)
        svc.request_export(uid, "audit")
        items, total = svc.list_by_user(uid)
        assert total == 1

    def test_list_all(self, db):
        svc = ComplianceService(db)
        svc.request_export(uuid.uuid4(), "audit")
        svc.request_export(uuid.uuid4(), "access_log")
        items, total = svc.list_all()
        assert total == 2

    def test_get_export_dir(self, db, tmp_path, monkeypatch):
        svc = ComplianceService(db)
        monkeypatch.setattr(svc.settings, "COMPLIANCE_EXPORT_DIR", str(tmp_path / "exports"))
        d = svc.get_export_dir()
        assert d.endswith("exports")


# =====================================================================
# 10. MonitoringService Tests
# =====================================================================

class TestMonitoringService:

    def test_record_metric(self, db):
        svc = MonitoringService(db)
        metric = svc.record_metric(MetricCategory.API_LATENCY, 12.5, "ms", "/test", "GET", 200)
        assert metric.id is not None
        assert metric.value == 12.5

    def test_record_api_latency(self, db):
        svc = MonitoringService(db)
        metric = svc.record_api_latency("/api/v1/issues", "POST", 55.3, 201)
        assert metric.category == MetricCategory.API_LATENCY
        assert metric.status_code == 201

    def test_record_sync_latency(self, db):
        svc = MonitoringService(db)
        metric = svc.record_sync_latency(120.0, "edge-1")
        assert metric.category == MetricCategory.SYNC_LATENCY
        assert metric.node_id == "edge-1"

    def test_list_by_category(self, db):
        _make_metric(db, category=MetricCategory.DB_QUERY)
        _make_metric(db, category=MetricCategory.API_LATENCY)
        svc = MonitoringService(db)
        items, total = svc.list_by_category(MetricCategory.DB_QUERY)
        assert total == 1

    def test_list_by_endpoint(self, db):
        _make_metric(db, endpoint="/api/v1/issues")
        svc = MonitoringService(db)
        items = svc.list_by_endpoint("/api/v1/issues")
        assert len(items) == 1

    def test_recent_metrics(self, db):
        _make_metric(db)
        _make_metric(db)
        svc = MonitoringService(db)
        items = svc.recent_metrics(limit=5)
        assert len(items) == 2

    def test_average_latency(self, db):
        _make_metric(db, category=MetricCategory.API_LATENCY, value=10)
        _make_metric(db, category=MetricCategory.API_LATENCY, value=30)
        svc = MonitoringService(db)
        avg = svc.average_latency(MetricCategory.API_LATENCY)
        assert avg == pytest.approx(20.0)

    def test_health_check_healthy(self, db):
        svc = MonitoringService(db)
        result = svc.health_check()
        assert result["status"] == "healthy"
        assert result["db_connected"] is True


# =====================================================================
# 11. Rate Limiter Middleware Unit Tests
# =====================================================================

class TestRateLimiter:

    def setup_method(self):
        reset_rate_limiter()

    def test_not_limited_under_threshold(self):
        assert _is_rate_limited("10.0.0.1", max_requests=5, window_seconds=60) is False

    def test_limited_over_threshold(self):
        for _ in range(5):
            _is_rate_limited("10.0.0.2", max_requests=5, window_seconds=60)
        assert _is_rate_limited("10.0.0.2", max_requests=5, window_seconds=60) is True

    def test_different_ips_independent(self):
        for _ in range(5):
            _is_rate_limited("a", max_requests=5, window_seconds=60)
        assert _is_rate_limited("a", max_requests=5, window_seconds=60) is True
        assert _is_rate_limited("b", max_requests=5, window_seconds=60) is False

    def test_reset_clears_store(self):
        for _ in range(10):
            _is_rate_limited("c", max_requests=5, window_seconds=60)
        reset_rate_limiter()
        assert _is_rate_limited("c", max_requests=5, window_seconds=60) is False


# =====================================================================
# 12. Integration — Offline → Sync Queue Flow
# =====================================================================

class TestOfflineToSyncIntegration:

    def test_end_to_end_flow(self, db):
        """
        Scenario: user creates an issue offline → promote to queue →
        begin sync → complete sync.
        """
        offline_svc = OfflineService(db)
        sync_svc = SyncService(db)

        # 1. Cache offline action
        action = offline_svc.cache_action(
            node_id="edge-1", user_id=uuid.uuid4(),
            action_type="create_issue", resource_type="issue",
            resource_id=uuid.uuid4(), payload={"title": "Offline Issue"},
        )
        assert action.status == OfflineStatus.CACHED

        # 2. Promote to sync queue
        promoted = offline_svc.promote_to_queue(action.id)
        assert promoted.status == OfflineStatus.QUEUED

        # 3. Verify sync entry
        pending, total = sync_svc.list_pending()
        assert total == 1
        sync_entry = pending[0]
        assert sync_entry.status == SyncStatus.PENDING

        # 4. Begin sync
        in_progress = sync_svc.begin_sync(sync_entry.id)
        assert in_progress.status == SyncStatus.IN_PROGRESS

        # 5. Complete sync
        done = sync_svc.complete_sync(sync_entry.id)
        assert done.status == SyncStatus.SYNCED
        assert done.synced_at is not None

    def test_conflict_resolution_flow(self, db):
        """Sync entry hits a conflict, gets resolved."""
        sync_svc = SyncService(db)

        entry = sync_svc.enqueue(
            "edge-1", SyncOperation.UPDATE, "citizen", uuid.uuid4(),
            payload={"name": "local"},
        )
        conflict = sync_svc.raise_conflict(
            entry.id, {"name": "local"}, {"name": "server"},
        )
        assert conflict.resolution == ConflictResolution.PENDING

        resolved = sync_svc.resolve_conflict(
            conflict.id, ConflictResolution.SERVER_WINS, notes="server is newer",
        )
        assert resolved.resolution == ConflictResolution.SERVER_WINS
        assert resolved.resolved_at is not None


# =====================================================================
# 13. Import Smoke Tests
# =====================================================================

class TestImports:

    def test_all_repositories_importable(self):
        from app.sync.repository import SyncQueueRepository
        from app.sync.conflict_repository import ConflictLogRepository
        from app.offline.repository import OfflineActionRepository
        from app.compliance.repository import ComplianceExportRepository
        from app.monitoring.repository import PerformanceMetricRepository
        from app.hardening.repository import RateLimitRepository
        assert all([
            SyncQueueRepository, ConflictLogRepository, OfflineActionRepository,
            ComplianceExportRepository, PerformanceMetricRepository, RateLimitRepository,
        ])

    def test_all_services_importable(self):
        from app.sync.service import SyncService
        from app.offline.service import OfflineService
        from app.compliance.service import ComplianceService
        from app.monitoring.service import MonitoringService
        assert all([SyncService, OfflineService, ComplianceService, MonitoringService])

    def test_rate_limiter_importable(self):
        from app.hardening.rate_limiter import RateLimitMiddleware, reset_rate_limiter
        assert RateLimitMiddleware is not None
        assert reset_rate_limiter is not None
