import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from beanie import PydanticObjectId, init_beanie
from mongomock_motor import AsyncMongoMockClient

from src.modules.dam.models import Asset, AssetStatus, Link, Album
from src.modules.dam.services.vector_service import VectorService
from src.modules.dam.services.pipeline_orchestrator import PipelineOrchestrator
from src.modules.dam.processors.clip_processor import CLIPProcessor
from src.modules.dam.processors.blip_processor import BLIPProcessor

@pytest.fixture(autouse=True)
async def mock_db():
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client.get_database("test_db"),
        document_models=[Asset, Link, Album]
    )

@pytest.fixture
def vector_service():
    # Mock QdrantClient to avoid real connections
    with patch("src.modules.dam.services.vector_service.QdrantClient"):
        svc = VectorService(url="http://mock:6333")
        svc._available = True
        return svc

@pytest.fixture
def orchestrator():
    return PipelineOrchestrator()

@pytest.mark.asyncio
async def test_vector_service_upsert(vector_service):
    asset = Asset(
        filename="test.jpg",
        storage_urn="fs://local/test.jpg",
        owner_id=PydanticObjectId()
    )
    await asset.save()
    
    vector = [0.1] * 512
    await vector_service.upsert_asset(asset, vector)
    
    # Check if asset was updated in DB
    reloaded = await Asset.get(asset.id)
    assert reloaded.vectors["clip"] == vector
    assert reloaded.vectors_indexed["clip"] is True
    
    # Verify Qdrant upsert was called
    vector_service.client.upsert.assert_called_once()

@pytest.mark.asyncio
async def test_pipeline_orchestrator_run(orchestrator):
    asset = Asset(
        filename="ai_test.jpg",
        storage_urn="fs://local/ai_test.jpg",
        owner_id=PydanticObjectId(),
        asset_types=["image"]
    )
    await asset.save()
    
    # Create mock processor
    mock_processor = MagicMock()
    mock_processor.name = "mock_p"
    mock_processor.applies_to = ["image"]
    mock_processor.process = AsyncMock()
    
    orchestrator.register_processor(mock_processor)
    await orchestrator.run(asset.id)
    
    mock_processor.process.assert_called_once()
    
    reloaded = await Asset.get(asset.id)
    assert reloaded.status == AssetStatus.READY

@pytest.mark.asyncio
async def test_clip_processor_integration(vector_service):
    # Mock model getter and storage_manager
    with patch.object(CLIPProcessor, "get_model") as mock_get_model, \
         patch("src.modules.dam.processors.clip_processor.storage_manager") as mock_storage, \
         patch("PIL.Image.open") as mock_img_open, \
         patch("src.core.registry.ServiceRegistry.get") as mock_reg_get:
        
        mock_reg_get.return_value = vector_service
        mock_storage.read_file = AsyncMock(return_value=b"fake_bytes")
        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock(tolist=lambda: [0.1] * 512)
        mock_get_model.return_value = mock_model
        
        processor = CLIPProcessor()
        asset = Asset(
            filename="clip.jpg",
            storage_urn="fs://local/clip.jpg",
            owner_id=PydanticObjectId(),
            asset_types=["image"]
        )
        await asset.save()
        
        await processor.process(asset)
        
        # Verify vector was indexed in Qdrant (via vector_service mock)
        vector_service.client.upsert.assert_called()
        
        reloaded = await Asset.get(asset.id)
        assert len(reloaded.vectors["clip"]) == 512
