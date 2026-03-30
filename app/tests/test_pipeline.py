import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.main import app


@pytest.fixture
def auth_headers() -> dict[str, str]:
    token = create_access_token(data={"sub": "1", "login": "testuser"})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_run_pipeline_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/pipeline/run", json={"topic": "AI", "user_id": "1"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_chat_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/pipeline/chat", json={"message": "hello"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_chat_with_auth(auth_headers: dict[str, str]):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/pipeline/chat",
            json={"message": "hello"},
            headers=auth_headers,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
