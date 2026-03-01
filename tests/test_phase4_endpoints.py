"""
NAYAM (नयम्) — Phase 4 Step 3 Endpoint Tests.

HTTP-level tests for all Phase 4 API routes: sync, offline,
compliance, monitoring, hardening.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.sync.models import SyncOperation, SyncStatus
from app.sync.conflict_model import ConflictResolution
from app.offline.models import OfflineStatus
from app.compliance.models import ExportFormat, ExportStatus
from app.monitoring.models import MetricCategory


# =====================================================================
#  1. Sync Endpoints
# =====================================================================

class TestSyncQueueEndpoints:

    def test_enqueue(self, client: TestClient, auth_headers_leader: dict):
        resp = client.post(
            "/api/v1/sync/queue",
            json={
                "node_id": "edge-1",
                "operation": "create",
                "resource_type": "issue",
                "resource_id": str(uuid.uuid4()),
                "payload": {"title": "offline issue"},
                "priority": 3,
            },
            headers=auth_headers_leader,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        assert data["node_id"] == "edge-1"
        assert data["priority"] == 3

    def test_enqueue_unauthenticated(self, client: TestClient):
        resp = client.post(
            "/api/v1/sync/queue",
            json={
                "node_id": "e",
                "operation": "create",
                "resource_type": "issue",
                "resource_id": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 401

    def test_list_pending(self, client: TestClient, auth_headers_leader: dict):
        # Enqueue two entries
        for _ in range(2):
            client.post(
                "/api/v1/sync/queue",
                json={
                    "node_id": "edge-1",
                    "operation": "create",
                    "resource_type": "issue",
                    "resource_id": str(uuid.uuid4()),
                },
                headers=auth_headers_leader,
            )
        resp = client.get("/api/v1/sync/queue", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_list_pending_by_node(self, client: TestClient, auth_headers_leader: dict):
        client.post(
            "/api/v1/sync/queue",
            json={"node_id": "a", "operation": "create", "resource_type": "issue", "resource_id": str(uuid.uuid4())},
            headers=auth_headers_leader,
        )
        client.post(
            "/api/v1/sync/queue",
            json={"node_id": "b", "operation": "create", "resource_type": "issue", "resource_id": str(uuid.uuid4())},
            headers=auth_headers_leader,
        )
        resp = client.get("/api/v1/sync/queue?node_id=a", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_status_summary(self, client: TestClient, auth_headers_leader: dict):
        client.post(
            "/api/v1/sync/queue",
            json={"node_id": "e", "operation": "create", "resource_type": "issue", "resource_id": str(uuid.uuid4())},
            headers=auth_headers_leader,
        )
        resp = client.get("/api/v1/sync/queue/status", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert "pending" in resp.json()["summary"]

    def test_get_sync_entry(self, client: TestClient, auth_headers_leader: dict):
        r = client.post(
            "/api/v1/sync/queue",
            json={"node_id": "e", "operation": "update", "resource_type": "citizen", "resource_id": str(uuid.uuid4())},
            headers=auth_headers_leader,
        )
        sync_id = r.json()["id"]
        resp = client.get(f"/api/v1/sync/queue/{sync_id}", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["id"] == sync_id

    def test_get_sync_entry_not_found(self, client: TestClient, auth_headers_leader: dict):
        resp = client.get(f"/api/v1/sync/queue/{uuid.uuid4()}", headers=auth_headers_leader)
        assert resp.status_code == 404


class TestSyncLifecycleEndpoints:

    def _enqueue(self, client, headers):
        r = client.post(
            "/api/v1/sync/queue",
            json={"node_id": "e", "operation": "create", "resource_type": "issue", "resource_id": str(uuid.uuid4())},
            headers=headers,
        )
        return r.json()["id"]

    def test_begin_sync(self, client: TestClient, auth_headers_leader: dict):
        sid = self._enqueue(client, auth_headers_leader)
        resp = client.post(f"/api/v1/sync/queue/{sid}/begin", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    def test_complete_sync(self, client: TestClient, auth_headers_leader: dict):
        sid = self._enqueue(client, auth_headers_leader)
        client.post(f"/api/v1/sync/queue/{sid}/begin", headers=auth_headers_leader)
        resp = client.post(f"/api/v1/sync/queue/{sid}/complete", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["status"] == "synced"

    def test_fail_sync(self, client: TestClient, auth_headers_leader: dict):
        sid = self._enqueue(client, auth_headers_leader)
        client.post(f"/api/v1/sync/queue/{sid}/begin", headers=auth_headers_leader)
        resp = client.post(f"/api/v1/sync/queue/{sid}/fail?error=timeout", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["status"] == "failed"
        assert resp.json()["error_message"] == "timeout"

    def test_begin_sync_wrong_status(self, client: TestClient, auth_headers_leader: dict):
        sid = self._enqueue(client, auth_headers_leader)
        client.post(f"/api/v1/sync/queue/{sid}/begin", headers=auth_headers_leader)
        # Already in_progress, trying begin again should 409
        resp = client.post(f"/api/v1/sync/queue/{sid}/begin", headers=auth_headers_leader)
        assert resp.status_code == 409

    def test_retry_failed(self, client: TestClient, auth_headers_leader: dict):
        sid = self._enqueue(client, auth_headers_leader)
        client.post(f"/api/v1/sync/queue/{sid}/begin", headers=auth_headers_leader)
        client.post(f"/api/v1/sync/queue/{sid}/fail?error=err", headers=auth_headers_leader)
        resp = client.post("/api/v1/sync/queue/retry", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_verify_checksum(self, client: TestClient, auth_headers_leader: dict):
        r = client.post(
            "/api/v1/sync/queue",
            json={"node_id": "e", "operation": "create", "resource_type": "issue",
                  "resource_id": str(uuid.uuid4()), "payload": {"k": "v"}},
            headers=auth_headers_leader,
        )
        sid = r.json()["id"]
        resp = client.get(f"/api/v1/sync/queue/{sid}/verify", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["checksum_valid"] is True


class TestConflictEndpoints:

    def test_list_conflicts_empty(self, client: TestClient, auth_headers_leader: dict):
        resp = client.get("/api/v1/sync/conflicts", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_resolve_conflict(self, client: TestClient, auth_headers_leader: dict, db_session):
        """Create a conflict in the DB, then resolve via API."""
        from app.sync.models import SyncQueue, SyncOperation
        from app.sync.conflict_model import ConflictLog

        se = SyncQueue(
            node_id="e", operation=SyncOperation.UPDATE,
            resource_type="citizen", resource_id=uuid.uuid4(),
            version=1, checksum="x",
        )
        db_session.add(se)
        db_session.commit()
        db_session.refresh(se)

        conflict = ConflictLog(
            sync_queue_id=se.id, node_id="e",
            resource_type="citizen", resource_id=se.resource_id,
            local_data={"a": 1}, server_data={"a": 2},
        )
        db_session.add(conflict)
        db_session.commit()
        db_session.refresh(conflict)

        resp = client.post(
            f"/api/v1/sync/conflicts/{conflict.id}/resolve",
            json={"resolution": "server_wins", "notes": "fresher data"},
            headers=auth_headers_leader,
        )
        assert resp.status_code == 200
        assert resp.json()["resolution"] == "server_wins"

    def test_resolve_conflict_not_found(self, client: TestClient, auth_headers_leader: dict):
        resp = client.post(
            f"/api/v1/sync/conflicts/{uuid.uuid4()}/resolve",
            json={"resolution": "local_wins"},
            headers=auth_headers_leader,
        )
        assert resp.status_code == 404


# =====================================================================
#  2. Offline Endpoints
# =====================================================================

class TestOfflineEndpoints:

    def test_cache_action(self, client: TestClient, auth_headers_leader: dict):
        resp = client.post(
            "/api/v1/offline/actions",
            json={
                "node_id": "edge-1",
                "action_type": "create_issue",
                "resource_type": "issue",
                "payload": {"title": "offline test"},
            },
            headers=auth_headers_leader,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "cached"
        assert data["checksum"] is not None

    def test_cache_action_unauthenticated(self, client: TestClient):
        resp = client.post(
            "/api/v1/offline/actions",
            json={"node_id": "e", "action_type": "x", "resource_type": "y"},
        )
        assert resp.status_code == 401

    def test_list_cached(self, client: TestClient, auth_headers_leader: dict):
        client.post(
            "/api/v1/offline/actions",
            json={"node_id": "e", "action_type": "create_issue", "resource_type": "issue"},
            headers=auth_headers_leader,
        )
        resp = client.get("/api/v1/offline/actions", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_get_action(self, client: TestClient, auth_headers_leader: dict):
        r = client.post(
            "/api/v1/offline/actions",
            json={"node_id": "e", "action_type": "x", "resource_type": "y"},
            headers=auth_headers_leader,
        )
        aid = r.json()["id"]
        resp = client.get(f"/api/v1/offline/actions/{aid}", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["id"] == aid

    def test_get_action_not_found(self, client: TestClient, auth_headers_leader: dict):
        resp = client.get(f"/api/v1/offline/actions/{uuid.uuid4()}", headers=auth_headers_leader)
        assert resp.status_code == 404

    def test_promote_action(self, client: TestClient, auth_headers_leader: dict):
        r = client.post(
            "/api/v1/offline/actions",
            json={"node_id": "e", "action_type": "create_issue", "resource_type": "issue",
                  "resource_id": str(uuid.uuid4()), "payload": {"a": 1}},
            headers=auth_headers_leader,
        )
        aid = r.json()["id"]
        resp = client.post(f"/api/v1/offline/actions/{aid}/promote", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"

    def test_promote_wrong_status(self, client: TestClient, auth_headers_leader: dict):
        r = client.post(
            "/api/v1/offline/actions",
            json={"node_id": "e", "action_type": "create_issue", "resource_type": "issue",
                  "resource_id": str(uuid.uuid4())},
            headers=auth_headers_leader,
        )
        aid = r.json()["id"]
        client.post(f"/api/v1/offline/actions/{aid}/promote", headers=auth_headers_leader)
        # Already queued
        resp = client.post(f"/api/v1/offline/actions/{aid}/promote", headers=auth_headers_leader)
        assert resp.status_code == 409

    def test_promote_all(self, client: TestClient, auth_headers_leader: dict):
        for _ in range(3):
            client.post(
                "/api/v1/offline/actions",
                json={"node_id": "e", "action_type": "create_issue", "resource_type": "issue",
                      "resource_id": str(uuid.uuid4()), "payload": {"x": 1}},
                headers=auth_headers_leader,
            )
        resp = client.post("/api/v1/offline/actions/promote-all", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["promoted_count"] == 3

    def test_status_summary(self, client: TestClient, auth_headers_leader: dict):
        client.post(
            "/api/v1/offline/actions",
            json={"node_id": "e", "action_type": "x", "resource_type": "y"},
            headers=auth_headers_leader,
        )
        resp = client.get("/api/v1/offline/actions/status", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert "cached" in resp.json()["summary"]

    def test_verify_checksum(self, client: TestClient, auth_headers_leader: dict):
        r = client.post(
            "/api/v1/offline/actions",
            json={"node_id": "e", "action_type": "x", "resource_type": "y", "payload": {"k": "v"}},
            headers=auth_headers_leader,
        )
        aid = r.json()["id"]
        resp = client.get(f"/api/v1/offline/actions/{aid}/verify", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["checksum_valid"] is True


# =====================================================================
#  3. Compliance Endpoints
# =====================================================================

class TestComplianceEndpoints:

    def test_request_export_as_leader(self, client: TestClient, auth_headers_leader: dict):
        resp = client.post(
            "/api/v1/compliance/exports",
            json={"report_type": "audit_summary", "export_format": "csv"},
            headers=auth_headers_leader,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "requested"
        assert data["export_format"] == "csv"

    def test_request_export_as_analyst(self, client: TestClient, auth_headers_analyst: dict):
        resp = client.post(
            "/api/v1/compliance/exports",
            json={"report_type": "access_log"},
            headers=auth_headers_analyst,
        )
        assert resp.status_code == 201

    def test_request_export_as_staff_denied(self, client: TestClient, auth_headers_staff: dict):
        resp = client.post(
            "/api/v1/compliance/exports",
            json={"report_type": "audit"},
            headers=auth_headers_staff,
        )
        assert resp.status_code == 403

    def test_list_exports(self, client: TestClient, auth_headers_leader: dict):
        client.post(
            "/api/v1/compliance/exports",
            json={"report_type": "audit"},
            headers=auth_headers_leader,
        )
        resp = client.get("/api/v1/compliance/exports", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_my_exports(self, client: TestClient, auth_headers_leader: dict):
        client.post(
            "/api/v1/compliance/exports",
            json={"report_type": "audit"},
            headers=auth_headers_leader,
        )
        resp = client.get("/api/v1/compliance/exports/mine", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_get_export(self, client: TestClient, auth_headers_leader: dict):
        r = client.post(
            "/api/v1/compliance/exports",
            json={"report_type": "full_dump", "export_format": "json"},
            headers=auth_headers_leader,
        )
        eid = r.json()["id"]
        resp = client.get(f"/api/v1/compliance/exports/{eid}", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["report_type"] == "full_dump"

    def test_get_export_not_found(self, client: TestClient, auth_headers_leader: dict):
        resp = client.get(f"/api/v1/compliance/exports/{uuid.uuid4()}", headers=auth_headers_leader)
        assert resp.status_code == 404


# =====================================================================
#  4. Monitoring Endpoints
# =====================================================================

class TestMonitoringEndpoints:

    def test_record_metric(self, client: TestClient, auth_headers_leader: dict):
        resp = client.post(
            "/api/v1/monitoring/metrics",
            json={
                "category": "api_latency",
                "value": 42.5,
                "unit": "ms",
                "endpoint": "/api/v1/issues",
                "method": "GET",
                "status_code": 200,
            },
            headers=auth_headers_leader,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["value"] == 42.5
        assert data["category"] == "api_latency"

    def test_list_metrics(self, client: TestClient, auth_headers_leader: dict):
        client.post(
            "/api/v1/monitoring/metrics",
            json={"category": "api_latency", "value": 10.0},
            headers=auth_headers_leader,
        )
        resp = client.get("/api/v1/monitoring/metrics", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_list_metrics_by_category(self, client: TestClient, auth_headers_leader: dict):
        client.post(
            "/api/v1/monitoring/metrics",
            json={"category": "db_query", "value": 5.0},
            headers=auth_headers_leader,
        )
        client.post(
            "/api/v1/monitoring/metrics",
            json={"category": "api_latency", "value": 15.0},
            headers=auth_headers_leader,
        )
        resp = client.get("/api/v1/monitoring/metrics?category=db_query", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_average_metric(self, client: TestClient, auth_headers_leader: dict):
        for v in [10.0, 20.0, 30.0]:
            client.post(
                "/api/v1/monitoring/metrics",
                json={"category": "api_latency", "value": v},
                headers=auth_headers_leader,
            )
        resp = client.get("/api/v1/monitoring/metrics/average/api_latency", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["average"] == pytest.approx(20.0)

    def test_deep_health(self, client: TestClient):
        """Deep health endpoint requires no auth."""
        resp = client.get("/api/v1/monitoring/health/deep")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["db_connected"] is True

    def test_record_metric_unauthenticated(self, client: TestClient):
        resp = client.post(
            "/api/v1/monitoring/metrics",
            json={"category": "api_latency", "value": 1.0},
        )
        assert resp.status_code == 401


# =====================================================================
#  5. Hardening Endpoints
# =====================================================================

class TestHardeningEndpoints:

    def _seed_rate_records(self, db_session):
        from app.hardening.models import RateLimitRecord
        for i in range(3):
            rec = RateLimitRecord(
                client_ip=f"10.0.0.{i}",
                endpoint="/test",
                window_seconds=60,
                blocked=1 if i < 2 else 0,
            )
            db_session.add(rec)
        db_session.commit()

    def test_list_rate_limits(self, client: TestClient, auth_headers_leader: dict, db_session):
        self._seed_rate_records(db_session)
        resp = client.get("/api/v1/hardening/rate-limits", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["total"] == 3

    def test_list_rate_limits_denied_for_staff(self, client: TestClient, auth_headers_staff: dict):
        resp = client.get("/api/v1/hardening/rate-limits", headers=auth_headers_staff)
        assert resp.status_code == 403

    def test_list_blocked(self, client: TestClient, auth_headers_leader: dict, db_session):
        self._seed_rate_records(db_session)
        resp = client.get("/api/v1/hardening/rate-limits/blocked", headers=auth_headers_leader)
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_rate_limit_summary(self, client: TestClient, auth_headers_leader: dict, db_session):
        self._seed_rate_records(db_session)
        resp = client.get("/api/v1/hardening/rate-limits/summary", headers=auth_headers_leader)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_events"] == 3
        assert data["total_blocked"] == 2

    def test_top_offenders(self, client: TestClient, auth_headers_leader: dict, db_session):
        from app.hardening.models import RateLimitRecord
        for _ in range(5):
            db_session.add(RateLimitRecord(client_ip="bad_ip", endpoint="/x", window_seconds=60, blocked=1))
        for _ in range(2):
            db_session.add(RateLimitRecord(client_ip="ok_ip", endpoint="/x", window_seconds=60, blocked=1))
        db_session.commit()

        resp = client.get("/api/v1/hardening/rate-limits/top-offenders", headers=auth_headers_leader)
        assert resp.status_code == 200
        offenders = resp.json()["offenders"]
        assert len(offenders) >= 2
        assert offenders[0]["client_ip"] == "bad_ip"
        assert offenders[0]["blocked_count"] == 5


# =====================================================================
#  6. Integration — Full Offline→Sync via API
# =====================================================================

class TestOfflineSyncIntegrationAPI:

    def test_cache_promote_sync_flow(self, client: TestClient, auth_headers_leader: dict):
        """Full happy path: cache → promote → begin → complete."""
        # 1. Cache offline action
        r1 = client.post(
            "/api/v1/offline/actions",
            json={
                "node_id": "edge-1",
                "action_type": "create_issue",
                "resource_type": "issue",
                "resource_id": str(uuid.uuid4()),
                "payload": {"title": "Integration Test"},
            },
            headers=auth_headers_leader,
        )
        assert r1.status_code == 201
        action_id = r1.json()["id"]
        assert r1.json()["status"] == "cached"

        # 2. Promote to sync queue
        r2 = client.post(f"/api/v1/offline/actions/{action_id}/promote", headers=auth_headers_leader)
        assert r2.status_code == 200
        assert r2.json()["status"] == "queued"

        # 3. Verify sync entry was created
        r3 = client.get("/api/v1/sync/queue", headers=auth_headers_leader)
        assert r3.json()["total"] >= 1
        sync_id = r3.json()["entries"][0]["id"]

        # 4. Begin sync
        r4 = client.post(f"/api/v1/sync/queue/{sync_id}/begin", headers=auth_headers_leader)
        assert r4.json()["status"] == "in_progress"

        # 5. Complete sync
        r5 = client.post(f"/api/v1/sync/queue/{sync_id}/complete", headers=auth_headers_leader)
        assert r5.json()["status"] == "synced"
        assert r5.json()["synced_at"] is not None


# =====================================================================
#  7. Schema Validation Tests
# =====================================================================

class TestSchemaValidation:

    def test_sync_enqueue_invalid_operation(self, client: TestClient, auth_headers_leader: dict):
        resp = client.post(
            "/api/v1/sync/queue",
            json={"node_id": "e", "operation": "invalid_op", "resource_type": "x", "resource_id": str(uuid.uuid4())},
            headers=auth_headers_leader,
        )
        assert resp.status_code == 422

    def test_sync_enqueue_missing_required(self, client: TestClient, auth_headers_leader: dict):
        resp = client.post(
            "/api/v1/sync/queue",
            json={"node_id": "e"},
            headers=auth_headers_leader,
        )
        assert resp.status_code == 422

    def test_offline_cache_missing_required(self, client: TestClient, auth_headers_leader: dict):
        resp = client.post(
            "/api/v1/offline/actions",
            json={"node_id": "e"},
            headers=auth_headers_leader,
        )
        assert resp.status_code == 422

    def test_compliance_export_invalid_format(self, client: TestClient, auth_headers_leader: dict):
        resp = client.post(
            "/api/v1/compliance/exports",
            json={"report_type": "audit", "export_format": "docx"},
            headers=auth_headers_leader,
        )
        assert resp.status_code == 422

    def test_metric_negative_value(self, client: TestClient, auth_headers_leader: dict):
        resp = client.post(
            "/api/v1/monitoring/metrics",
            json={"category": "api_latency", "value": -1},
            headers=auth_headers_leader,
        )
        assert resp.status_code == 422
