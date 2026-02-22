import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from src.main import app

@pytest.mark.asyncio
async def test_get_types():
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/dam/types")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            types = [t["id"] for t in data]
            
            # Assert all 6 exist (5 builtin + 1 fallback)
            assert "image" in types
            assert "video" in types
            assert "audio" in types
            assert "document" in types
            assert "url" in types
            assert "other" in types
            assert len(data) == 6
