"""
NAYAM (नयम्) — Document Module Tests.

Tests for document upload, file validation, text extraction stub,
summary stub, and retrieval.
"""

import io
import uuid

import pytest
from fastapi.testclient import TestClient

from app.models.document import Document
from app.models.user import User
from app.services.document import extract_text, generate_summary, chunk_text


# ═══════════════════════════════════════════════════════════════════════
# TEXT EXTRACTION & PROCESSING TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestStubFunctions:
    """Tests for text extraction and summary functions."""

    def test_extract_text_returns_string(self) -> None:
        """extract_text should return a string for unsupported types."""
        result = extract_text("/path/to/test.xyz")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_extract_text_txt_file(self, tmp_path) -> None:
        """extract_text should read .txt files."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello world test content")
        result = extract_text(str(txt_file))
        assert "Hello world" in result

    def test_generate_summary_returns_string(self) -> None:
        """generate_summary should return a string."""
        result = generate_summary("Some extracted text here. This is a test document. It has content.")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_chunk_text_basic(self) -> None:
        """chunk_text should split long text into chunks."""
        text = " ".join([f"word{i}" for i in range(1000)])
        chunks = chunk_text(text, chunk_size=100, overlap=10)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) > 0

    def test_chunk_text_short(self) -> None:
        """chunk_text should return single chunk for short text."""
        text = "Short text"
        chunks = chunk_text(text)
        assert len(chunks) == 1


# ═══════════════════════════════════════════════════════════════════════
# UPLOAD DOCUMENT TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestUploadDocument:
    """Tests for POST /api/v1/documents/upload."""

    def test_upload_pdf_success(
        self, client: TestClient, auth_headers_leader: dict
    ) -> None:
        """Uploading a valid PDF should succeed."""
        file_content = b"%PDF-1.4 test content"
        response = client.post(
            "/api/v1/documents/upload",
            data={"title": "Test Report"},
            files={"file": ("report.pdf", io.BytesIO(file_content), "application/pdf")},
            headers=auth_headers_leader,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Report"
        assert data["extracted_text"] is not None
        assert data["summary"] is not None

    def test_upload_txt_success(
        self, client: TestClient, auth_headers_staff: dict
    ) -> None:
        """Uploading a valid TXT file should succeed."""
        file_content = b"This is a plain text document for testing."
        response = client.post(
            "/api/v1/documents/upload",
            data={"title": "Text Notes"},
            files={"file": ("notes.txt", io.BytesIO(file_content), "text/plain")},
            headers=auth_headers_staff,
        )
        assert response.status_code == 201

    def test_upload_disallowed_extension(
        self, client: TestClient, auth_headers_leader: dict
    ) -> None:
        """Uploading a file with disallowed extension should return 400."""
        file_content = b"#!/bin/bash\necho hacked"
        response = client.post(
            "/api/v1/documents/upload",
            data={"title": "Malicious Script"},
            files={"file": ("script.sh", io.BytesIO(file_content), "application/x-sh")},
            headers=auth_headers_leader,
        )
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]

    def test_upload_exe_blocked(
        self, client: TestClient, auth_headers_leader: dict
    ) -> None:
        """Uploading .exe file should be blocked."""
        file_content = b"MZ executable content"
        response = client.post(
            "/api/v1/documents/upload",
            data={"title": "Executable"},
            files={"file": ("virus.exe", io.BytesIO(file_content), "application/octet-stream")},
            headers=auth_headers_leader,
        )
        assert response.status_code == 400

    def test_upload_missing_title(
        self, client: TestClient, auth_headers_leader: dict
    ) -> None:
        """Upload without title should return 422."""
        file_content = b"Some file content"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("doc.pdf", io.BytesIO(file_content), "application/pdf")},
            headers=auth_headers_leader,
        )
        assert response.status_code == 422

    def test_upload_analyst_denied(
        self, client: TestClient, auth_headers_analyst: dict
    ) -> None:
        """Analyst should not be able to upload documents."""
        file_content = b"Some content"
        response = client.post(
            "/api/v1/documents/upload",
            data={"title": "Should Fail"},
            files={"file": ("doc.pdf", io.BytesIO(file_content), "application/pdf")},
            headers=auth_headers_analyst,
        )
        assert response.status_code == 403


# ═══════════════════════════════════════════════════════════════════════
# LIST / GET DOCUMENT TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestListDocuments:
    """Tests for GET /api/v1/documents/."""

    def test_list_documents_empty(
        self, client: TestClient, auth_headers_leader: dict
    ) -> None:
        """Empty document list should return total=0."""
        response = client.get("/api/v1/documents/", headers=auth_headers_leader)
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_list_documents_with_data(
        self, client: TestClient, auth_headers_leader: dict, sample_document: Document
    ) -> None:
        """List should include existing documents."""
        response = client.get("/api/v1/documents/", headers=auth_headers_leader)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["documents"][0]["title"] == "Test Document"


class TestGetDocument:
    """Tests for GET /api/v1/documents/{document_id}."""

    def test_get_document_success(
        self, client: TestClient, auth_headers_leader: dict, sample_document: Document
    ) -> None:
        """Get document by valid ID should return the document."""
        response = client.get(
            f"/api/v1/documents/{sample_document.id}",
            headers=auth_headers_leader,
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Test Document"

    def test_get_document_not_found(
        self, client: TestClient, auth_headers_leader: dict
    ) -> None:
        """Get non-existent document should return 404."""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/documents/{fake_id}",
            headers=auth_headers_leader,
        )
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════
# DELETE DOCUMENT TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestDeleteDocument:
    """Tests for DELETE /api/v1/documents/{document_id}."""

    def test_delete_document_as_leader(
        self, client: TestClient, auth_headers_leader: dict, sample_document: Document
    ) -> None:
        """Leader should be able to delete a document."""
        response = client.delete(
            f"/api/v1/documents/{sample_document.id}",
            headers=auth_headers_leader,
        )
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    def test_delete_document_as_staff_denied(
        self, client: TestClient, auth_headers_staff: dict, sample_document: Document
    ) -> None:
        """Staff should not be able to delete documents (Leader only)."""
        response = client.delete(
            f"/api/v1/documents/{sample_document.id}",
            headers=auth_headers_staff,
        )
        assert response.status_code == 403

    def test_delete_nonexistent_document(
        self, client: TestClient, auth_headers_leader: dict
    ) -> None:
        """Deleting non-existent document should return 404."""
        fake_id = uuid.uuid4()
        response = client.delete(
            f"/api/v1/documents/{fake_id}",
            headers=auth_headers_leader,
        )
        assert response.status_code == 404
