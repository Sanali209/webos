import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from beanie import PydanticObjectId, init_beanie
from httpx import AsyncClient, ASGITransport
import numpy as np
from mongomock_motor import AsyncMongoMockClient

from src.main import app
from src.modules.dam.models import Asset, AssetStatus, Link, Album
from src.core.registry import ServiceRegistry
from src.modules.dam.services.pipeline_orchestrator import PipelineOrchestrator

# Valid 24-char hex strings for ObjectIds
TEST_OWNER_ID = PydanticObjectId("65d4f1234567890abcde1234")

@pytest_asyncio.fixture
async def mock_db():
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client.get_database("test"), 
        document_models=[Asset, Link, Album]
    )
    yield

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture(autouse=True)
async def registry_setup():
    from src.modules.dam.hooks import hooks
    from src.core.services.settings_service import settings_service
    from src.modules.dam.settings import DAMSettings
    
    # Pre-register settings so hooks.register_services doesn't fail
    settings_service._cache["dam"] = DAMSettings(system_owner_id=str(TEST_OWNER_ID))
    
    hooks.register_services()
    yield

@pytest.mark.asyncio
async def test_ai_processors_registration(mock_db):
    orchestrator = ServiceRegistry.get(PipelineOrchestrator)
    processor_names = [p.name for p in orchestrator.processors]
    
    assert "clip" in processor_names
    assert "blip" in processor_names
    assert "tagger" in processor_names
    assert "yolo_detector" in processor_names
    assert "structural_features" in processor_names
    assert "relation_analysis" in processor_names

@pytest.mark.asyncio
async def test_album_crud(client, mock_db):
    # 1. Create Album
    resp = await client.post("/api/dam/albums", json={"title": "Travel", "description": "Vacation photos"})
    assert resp.status_code == 201
    album_id = resp.json()["id"]
    
    # 2. List Albums
    resp = await client.get("/api/dam/albums")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    
    # 3. Add Asset (mock asset)
    asset = Asset(
        filename="test.jpg", 
        storage_urn="fs://local/test.jpg", 
        owner_id=TEST_OWNER_ID,
        asset_types=["image"]
    )
    await asset.insert()
    
    resp = await client.post(f"/api/dam/albums/{album_id}/assets/{asset.id}")
    assert resp.status_code == 200
    
    # 4. Verify count
    resp = await client.get(f"/api/dam/albums/{album_id}")
    assert resp.json()["asset_count"] == 1

@pytest.mark.asyncio
async def test_graph_links_endpoint(client, mock_db):
    aid1 = PydanticObjectId()
    aid2 = PydanticObjectId()
    
    link = Link(source_id=aid1, target_id=aid2, relation="visually_similar_to", weight=0.9)
    await link.insert()
    
    resp = await client.get(f"/api/dam/assets/{aid1}/links")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["target_id"] == str(aid2)
    assert data[0]["relation"] == "visually_similar_to"

@pytest.mark.asyncio
async def test_full_ai_pipeline_execution(mock_db):
    # Mocking storage and external ML calls to verify orchestration
    asset = Asset(
        filename="ai_test.jpg", 
        storage_urn="fs://local/ai_test.jpg", 
        owner_id=TEST_OWNER_ID,
        asset_types=["image"]
    )
    await asset.insert()
    
    orchestrator = ServiceRegistry.get(PipelineOrchestrator)
    
    # Patch all processors to avoid actual heavy model loads in unit test
    with patch("src.modules.dam.processors.clip_processor.CLIPProcessor.process") as m_clip, \
         patch("src.modules.dam.processors.blip_processor.BLIPProcessor.process") as m_blip, \
         patch("src.modules.dam.processors.tag_processor.TagProcessor.process") as m_tag, \
         patch("src.modules.dam.processors.detection_processor.DetectionProcessor.process") as m_det, \
         patch("src.modules.dam.processors.structural_processor.StructuralProcessor.process") as m_str, \
         patch("src.modules.dam.processors.relation_processor.VectorRelationProcessor.process") as m_rel:
        
        await orchestrator.run(asset.id)
        
        assert m_clip.called
        assert m_blip.called
        assert m_tag.called
        assert m_det.called
        assert m_str.called
        assert m_rel.called

@pytest.mark.asyncio
async def test_search_graph_expansion(client, mock_db):
    # Create seeds and linked assets
    aid1 = PydanticObjectId() # Result from keyword/vector
    aid2 = PydanticObjectId() # Neighbor in graph
    
    asset1 = Asset(
        id=aid1, filename="beach.jpg", storage_urn="fs://local/beach.jpg", 
        owner_id=TEST_OWNER_ID, title="Beach", asset_types=["image"]
    )
    asset2 = Asset(
        id=aid2, filename="ocean.jpg", storage_urn="fs://local/ocean.jpg", 
        owner_id=TEST_OWNER_ID, title="Ocean", asset_types=["image"]
    )
    await asset1.insert()
    await asset2.insert()
    
    # Link them
    link = Link(source_id=aid1, target_id=aid2, relation="visually_similar_to")
    await link.insert()
    
    from src.modules.dam.services.unified_search import UnifiedSearchService
    search_svc = ServiceRegistry.get(UnifiedSearchService)
    
    # Mock keyword/vector to return aid1
    with patch.object(UnifiedSearchService, "_keyword_channel", return_value=[str(aid1)]), \
         patch.object(UnifiedSearchService, "_vector_channel", return_value=[]):
        
        from src.modules.dam.schemas.search import SearchRequest, AssetFilter
        req = SearchRequest(query="Beach", filter=AssetFilter(owner_id=TEST_OWNER_ID))
        result = await search_svc.search(req)
        
        # Verify that aid2 (the neighbor) is in the results
        result_ids = [item.asset_id for item in result.items]
        assert str(aid1) in result_ids
        assert str(aid2) in result_ids
        
        # Identify aid2 as matched by "graph"
        aid2_hit = next(h for h in result.items if h.asset_id == str(aid2))
        assert "graph" in aid2_hit.matched_by
