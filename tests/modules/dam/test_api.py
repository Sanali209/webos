import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from beanie import init_beanie, PydanticObjectId
from mongomock_motor import AsyncMongoMockClient

from src.main import app
from src.core.registry import ServiceRegistry
from src.modules.dam.models import Asset, AssetStatus
from src.modules.dam.services.asset_service import AssetService
from src.modules.dam.services.unified_search import UnifiedSearchService

# Valid 24-char hex strings for ObjectIds
TEST_OWNER_ID = PydanticObjectId("65d4f1234567890abcde1234")

@pytest_asyncio.fixture
async def mock_db():
    client = AsyncMongoMockClient()
    await init_beanie(database=client.get_database("test"), document_models=[Asset])
    yield

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_asset_service():
    service = AsyncMock(spec=AssetService)
    return service

@pytest.fixture
def mock_search_service():
    service = AsyncMock(spec=UnifiedSearchService)
    return service

@pytest_asyncio.fixture(autouse=True)
async def registry_setup(mock_asset_service, mock_search_service):
    # Mocking settings to return a valid owner id string
    from src.modules.dam.settings import DAMSettings
    mock_settings = DAMSettings(system_owner_id=str(TEST_OWNER_ID))
    
    with patch("src.modules.dam.router.get_settings", return_value=mock_settings),          patch.object(ServiceRegistry, "get") as mock_get:
        
        def side_effect(interface):
            if interface == AssetService:
                return mock_asset_service
            if interface == UnifiedSearchService:
                return mock_search_service
            return MagicMock()
        
        mock_get.side_effect = side_effect
        yield

@pytest.mark.asyncio
async def test_get_types(client):
    response = await client.get("/api/dam/types")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

@pytest.mark.asyncio
async def test_upload_asset(client, mock_asset_service, mock_db):
    from src.modules.dam.models import Asset
    fake_asset = Asset(
        filename="test.jpg",
        storage_urn="fs://local/dam/test.jpg",
        owner_id=TEST_OWNER_ID,
        asset_types=["image"],
        status=AssetStatus.READY
    )
    mock_asset_service.ingest.return_value = fake_asset
    
    files = {"file": ("test.jpg", b"fake image content", "image/jpeg")}
    response = await client.post("/api/dam/assets", files=files)
    
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.jpg"
    assert data["primary_type"] == "image"
    mock_asset_service.ingest.assert_called_once()

@pytest.mark.asyncio
async def test_list_assets(client, mock_db):
    from src.modules.dam.models import Asset
    for i in range(3):
        await Asset(
            filename=f"test{i}.jpg",
            storage_urn=f"fs://local/dam/test{i}.jpg",
            owner_id=TEST_OWNER_ID,
            asset_types=["image"],
            status=AssetStatus.READY
        ).insert()
        
    response = await client.get("/api/dam/assets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

@pytest.mark.asyncio
async def test_get_asset_detail(client, mock_db):
    from src.modules.dam.models import Asset
    asset = Asset(
        filename="detail.jpg",
        storage_urn="fs://local/dam/detail.jpg",
        owner_id=TEST_OWNER_ID,
        asset_types=["image"],
        status=AssetStatus.READY
    )
    await asset.insert()
    
    response = await client.get(f"/api/dam/assets/{asset.id}")
    assert response.status_code == 200
    assert response.json()["filename"] == "detail.jpg"

@pytest.mark.asyncio
async def test_update_asset(client, mock_db):
    from src.modules.dam.models import Asset
    asset = Asset(
        filename="update.jpg",
        storage_urn="fs://local/dam/update.jpg",
        owner_id=TEST_OWNER_ID,
        asset_types=["image"],
        status=AssetStatus.READY
    )
    await asset.insert()
    
    payload = {"title": "New Title", "tags": ["tag1", "tag2"]}
    response = await client.patch(f"/api/dam/assets/{asset.id}", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert "tag1" in data["tags"]

@pytest.mark.asyncio
async def test_delete_asset(client, mock_asset_service):
    response = await client.delete(f"/api/dam/assets/{TEST_OWNER_ID}")
    assert response.status_code == 204
    mock_asset_service.delete.assert_called_once()

@pytest.mark.asyncio
async def test_search_assets(client, mock_search_service):
    from src.modules.dam.schemas.search import SearchPage, SearchHit
    mock_search_service.search.return_value = SearchPage(
        items=[SearchHit(asset_id="123", score=0.9, matched_by=["keyword"])],
        total_estimate=1
    )
    
    payload = {"query": "cat", "limit": 10}
    response = await client.post("/api/dam/search", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["asset_id"] == "123"

@pytest.mark.asyncio
async def test_pipeline_status(client, mock_db):
    from src.modules.dam.models import Asset
    await Asset(
        filename="p1.jpg", storage_urn="u1", owner_id=TEST_OWNER_ID, 
        asset_types=["i"], status=AssetStatus.READY
    ).insert()
    await Asset(
        filename="p2.jpg", storage_urn="u2", owner_id=TEST_OWNER_ID, 
        asset_types=["i"], status=AssetStatus.PENDING
    ).insert()
    
    response = await client.get("/api/dam/pipeline/status")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["ready"] == 1
    assert data["pending"] == 1

@pytest.mark.asyncio
async def test_download_asset(client, mock_db):
    from src.modules.dam.models import Asset
    from io import BytesIO
    asset = Asset(
        filename="test.txt",
        storage_urn="fs://local/dam/test.txt",
        owner_id=TEST_OWNER_ID,
        asset_types=["document"],
        status=AssetStatus.READY,
        mime_type="text/plain"
    )
    await asset.insert()
    
    mock_file = BytesIO(b"hello world")
    
    with patch("src.core.storage.storage_manager.open_file", return_value=mock_file):
        response = await client.get(f"/api/dam/assets/{asset.id}/download")
        assert response.status_code == 200
        assert response.content == b"hello world"
        assert response.headers["Content-Disposition"] == 'attachment; filename="test.txt"'
