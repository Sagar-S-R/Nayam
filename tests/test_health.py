"""
NAYAM (नयम्) — Health Check Tests.

Tests for the /health endpoint.
"""

from fastapi.testclient import TestClient


class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """Health check should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client: TestClient) -> None:
        """Health check should return correct structure."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data
        assert "environment" in data

    def test_health_app_name(self, client: TestClient) -> None:
        """Health check should return NAYAM as app name."""
        response = client.get("/health")
        assert response.json()["app"] == "NAYAM"
