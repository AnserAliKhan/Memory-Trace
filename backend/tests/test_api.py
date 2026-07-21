"""Tests for API endpoints."""

import json
import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestDocumentEndpoints:
    def test_import_url_validates_input(self, client):
        response = client.post(
            "/api/documents/import-url",
            json={"url": ""},
        )
        assert response.status_code == 422

    def test_import_file_without_file_rejects(self, client):
        response = client.post("/api/documents/import")
        assert response.status_code == 422

    def test_list_documents_returns_empty(self, client):
        response = client.get("/api/documents/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_delete_nonexistent_document(self, client):
        response = client.delete("/api/documents/99999")
        assert response.status_code == 404

    def test_import_txt_file(self, client):
        response = client.post(
            "/api/documents/import",
            files={"file": ("hello.txt", b"Hello world", "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["title"] == "hello.txt"
        assert data["source_type"] == "txt"
        assert data["chunks"] > 0

    def test_dedup_rejects_duplicate(self, client):
        content = b"Unique test content"
        response = client.post(
            "/api/documents/import",
            files={"file": ("dup.txt", content, "text/plain")},
        )
        assert response.status_code == 200
        doc_id = response.json()["document_id"]

        response2 = client.post(
            "/api/documents/import",
            files={"file": ("dup.txt", content, "text/plain")},
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["status"] == "duplicate"
        assert data2["document_id"] == doc_id

    def test_delete_removes_document(self, client):
        response = client.post(
            "/api/documents/import",
            files={"file": ("delme.txt", b"delete me", "text/plain")},
        )
        doc_id = response.json()["document_id"]

        del_resp = client.delete(f"/api/documents/{doc_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "deleted"

        get_resp = client.delete(f"/api/documents/{doc_id}")
        assert get_resp.status_code == 404


class TestQueryEndpoint:
    def test_empty_query_rejects(self, client):
        response = client.post(
            "/api/query/",
            json={"query": "   "},
        )
        assert response.status_code == 422

    def test_query_with_no_documents(self, client):
        response = client.post(
            "/api/query/",
            json={"query": "test query"},
        )
        assert response.status_code == 200
        lines = [l for l in response.text.strip().split("\n") if l]
        assert len(lines) >= 1
        first = json.loads(lines[0])
        assert "token" in first or "sources" in first

    def test_query_after_import(self, client):
        client.post(
            "/api/documents/import",
            files={"file": ("ml.txt", b"Machine learning is a subset of artificial intelligence.", "text/plain")},
        )

        response = client.post(
            "/api/query/",
            json={"query": "What is machine learning?"},
        )
        assert response.status_code == 200
        lines = response.text.strip().split("\n")
        assert len(lines) >= 1
        final = json.loads(lines[-1])
        assert "sources" in final
        assert "duration_ms" in final

    def test_history_endpoint(self, client):
        response = client.get("/api/query/history")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestSettingsEndpoint:
    def test_settings_returns_stub(self, client):
        response = client.get("/api/settings")
        assert response.status_code in (200, 404)
