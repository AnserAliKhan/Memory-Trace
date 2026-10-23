"""CORS: hosted preview frontends may call the local backend; other sites may not."""

import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture(scope="module")
def client():
    # No `with`: preflight is answered by the middleware, lifespan isn't needed.
    return TestClient(create_app())


def preflight(client, origin: str):
    return client.options(
        "/api/health",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )


@pytest.mark.parametrize("origin", [
    "http://localhost:5173",
    "https://refound.pages.dev",
    "https://uat.refound.pages.dev",
    "https://abc123de.refound.pages.dev",
    "https://feat-new-ui.refound.pages.dev",
])
def test_allows_local_dev_and_project_previews(client, origin):
    response = preflight(client, origin)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


@pytest.mark.parametrize("origin", [
    "https://evil.pages.dev",
    "https://refound.pages.dev.evil.com",
    "https://evil.com/?https://uat.refound.pages.dev",
    "http://uat.refound.pages.dev",
    "https://a.b.refound.pages.dev",
])
def test_rejects_other_origins(client, origin):
    response = preflight(client, origin)
    assert "access-control-allow-origin" not in response.headers
