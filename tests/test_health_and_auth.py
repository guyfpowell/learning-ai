import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def valid_api_key(monkeypatch):
    monkeypatch.setenv("AI_SERVICE_API_KEY", "test-key-abc")
    return "test-key-abc"


@pytest.fixture
async def client(valid_api_key):
    # Import app after env var is set so middleware picks up the key
    from main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


class TestHealthEndpoint:
    async def test_health_returns_200(self, client):
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_returns_ok_status(self, client):
        response = await client.get("/health")
        assert response.json() == {"status": "ok"}

    async def test_health_does_not_require_api_key(self, monkeypatch):
        monkeypatch.setenv("AI_SERVICE_API_KEY", "some-key")
        from main import app

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get("/health")
        assert response.status_code == 200


class TestAuthMiddleware:
    async def test_missing_api_key_returns_401(self, client):
        response = await client.get("/generate/")
        assert response.status_code == 401

    async def test_wrong_api_key_returns_401(self, client):
        response = await client.get(
            "/generate/", headers={"X-Internal-API-Key": "wrong-key"}
        )
        assert response.status_code == 401

    async def test_valid_api_key_passes_auth(self, client, valid_api_key):
        # A valid key should not produce a 401 (even if the route doesn't exist yet)
        response = await client.get(
            "/generate/", headers={"X-Internal-API-Key": valid_api_key}
        )
        assert response.status_code != 401

    async def test_empty_api_key_env_var_returns_401(self, monkeypatch):
        monkeypatch.setenv("AI_SERVICE_API_KEY", "")
        from main import app

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/generate/", headers={"X-Internal-API-Key": "any-value"}
            )
        assert response.status_code == 401

    async def test_401_response_body(self, client):
        response = await client.get("/generate/")
        assert response.json() == {"detail": "Unauthorized"}
