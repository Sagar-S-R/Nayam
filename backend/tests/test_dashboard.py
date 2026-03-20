"""
NAYAM (नयम्) — Dashboard Module Tests.

Tests for the dashboard aggregation endpoint.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.citizen import Citizen
from app.models.document import Document
from app.models.issue import Issue, IssueStatus, IssuePriority
from app.models.user import User


# ═══════════════════════════════════════════════════════════════════════
# DASHBOARD AGGREGATION TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestDashboard:
    """Tests for GET /api/v1/dashboard/."""

    def test_dashboard_empty(
        self, client: TestClient, auth_headers_leader: dict
    ) -> None:
        """Dashboard with no data should return zero counts."""
        response = client.get("/api/v1/dashboard/", headers=auth_headers_leader)
        assert response.status_code == 200
        data = response.json()
        assert data["total_issues"] == 0
        assert data["total_documents"] == 0
        assert data["issues_by_department"] == []
        assert data["issues_by_status"] == []
        assert data["recent_documents"] == []

    def test_dashboard_with_issues(
        self, client: TestClient, auth_headers_leader: dict, sample_issue: Issue
    ) -> None:
        """Dashboard should reflect existing issues."""
        response = client.get("/api/v1/dashboard/", headers=auth_headers_leader)
        assert response.status_code == 200
        data = response.json()
        assert data["total_issues"] == 1
        assert len(data["issues_by_department"]) == 1
        assert data["issues_by_department"][0]["department"] == "Water Supply"
        assert data["issues_by_department"][0]["count"] == 1
        assert len(data["issues_by_status"]) == 1
        assert data["issues_by_status"][0]["status"] == "Open"

    def test_dashboard_with_documents(
        self, client: TestClient, auth_headers_leader: dict, sample_document: Document
    ) -> None:
        """Dashboard should reflect existing documents."""
        response = client.get("/api/v1/dashboard/", headers=auth_headers_leader)
        assert response.status_code == 200
        data = response.json()
        assert data["total_documents"] == 1
        assert len(data["recent_documents"]) == 1
        assert data["recent_documents"][0]["title"] == "Test Document"

    def test_dashboard_multiple_issues(
        self,
        client: TestClient,
        auth_headers_leader: dict,
        db_session: Session,
        sample_citizen: Citizen,
    ) -> None:
        """Dashboard should correctly aggregate multiple issues across departments."""
        # Create issues in different departments with different statuses
        issues = [
            Issue(
                citizen_id=sample_citizen.id,
                department="Water Supply",
                description="Water issue number one in the ward area.",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
            ),
            Issue(
                citizen_id=sample_citizen.id,
                department="Water Supply",
                description="Water issue number two in the ward area.",
                status=IssueStatus.IN_PROGRESS,
                priority=IssuePriority.MEDIUM,
            ),
            Issue(
                citizen_id=sample_citizen.id,
                department="Road & Transport",
                description="Road damage issue in the main street area.",
                status=IssueStatus.OPEN,
                priority=IssuePriority.LOW,
            ),
            Issue(
                citizen_id=sample_citizen.id,
                department="Health",
                description="Health center needs more medical supplies urgently.",
                status=IssueStatus.CLOSED,
                priority=IssuePriority.HIGH,
            ),
        ]
        for issue in issues:
            db_session.add(issue)
        db_session.commit()

        response = client.get("/api/v1/dashboard/", headers=auth_headers_leader)
        assert response.status_code == 200
        data = response.json()

        assert data["total_issues"] == 4

        # Check department breakdown
        dept_counts = {d["department"]: d["count"] for d in data["issues_by_department"]}
        assert dept_counts["Water Supply"] == 2
        assert dept_counts["Road & Transport"] == 1
        assert dept_counts["Health"] == 1

        # Check status breakdown
        status_counts = {s["status"]: s["count"] for s in data["issues_by_status"]}
        assert status_counts["Open"] == 2
        assert status_counts["In Progress"] == 1
        assert status_counts["Closed"] == 1

    def test_dashboard_unauthenticated(self, client: TestClient) -> None:
        """Unauthenticated request should return 401."""
        response = client.get("/api/v1/dashboard/")
        assert response.status_code == 401

    def test_dashboard_analyst_access(
        self, client: TestClient, auth_headers_analyst: dict
    ) -> None:
        """Analyst should be able to access the dashboard."""
        response = client.get("/api/v1/dashboard/", headers=auth_headers_analyst)
        assert response.status_code == 200
