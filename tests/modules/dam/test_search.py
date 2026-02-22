import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from beanie import PydanticObjectId, init_beanie
from mongomock_motor import AsyncMongoMockClient

from src.modules.dam.models import Asset, Link, Album
from src.modules.dam.schemas.search import SearchRequest, AssetFilter
from src.modules.dam.services.unified_search import UnifiedSearchService
from src.modules.dam.services.vector_service import VectorService
from src.modules.dam.processors.clip_processor import CLIPProcessor
from src.core.registry import ServiceRegistry

@pytest.fixture(autouse=True)
async def mock_db():
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client.get_database("test_db"),
        document_models=[Asset, Link, Album]
    )

@pytest.fixture
def vector_service():
    with patch("src.modules.dam.services.vector_service.QdrantClient"):
        svc = VectorService(url="http://mock:6333")
        svc._available = True
        return svc

@pytest.fixture
def search_service():
    return UnifiedSearchService()

@pytest.mark.asyncio
async def test_search_list_filtered(search_service):
    # Setup: Create some assets
    owner_id = PydanticObjectId()
    for i in range(5):
        await Asset(
            filename=f"image_{i}.jpg",
            storage_urn=f"fs://local/{i}.jpg",
            owner_id=owner_id,
            asset_types=["image"],
            tags=["holiday"] if i < 3 else ["work"]
        ).save()
        
    request = SearchRequest(
        filter=AssetFilter(owner_id=owner_id, tags=["holiday"]),
        include_facets=True
    )
    
    with patch.object(search_service, "_compute_facets", new_callable=AsyncMock) as mock_facets:
        from src.modules.dam.schemas.search import SearchFacets, FacetBucket
        mock_facets.return_value = SearchFacets(asset_types=[FacetBucket(key="image", count=3)])
        
        page = await search_service.search(request)
        
        assert len(page.items) == 3
        assert page.facets is not None
        assert page.facets.asset_types[0].key == "image"
        mock_facets.assert_called_once()

@pytest.mark.asyncio
async def test_hybrid_search_fusion(search_service, vector_service):
    owner_id = PydanticObjectId()
    asset1 = await Asset(filename="cat.jpg", storage_urn="fs://1", owner_id=owner_id).save()
    asset2 = await Asset(filename="dog.jpg", storage_urn="fs://2", owner_id=owner_id).save()
    
    # Mock channels to return specific results
    with patch.object(search_service, "_keyword_channel", new_callable=AsyncMock) as mock_keyword, \
         patch.object(search_service, "_vector_channel", new_callable=AsyncMock) as mock_vector:
         
        # Keyword channel ranks asset1 first
        mock_keyword.return_value = [str(asset1.id), str(asset2.id)]
        # Vector channel ranks asset2 first
        mock_vector.return_value = [str(asset2.id), str(asset1.id)]
        
        request = SearchRequest(query="find animals", filter=AssetFilter(owner_id=owner_id))
        page = await search_service.search(request)
        
        assert len(page.items) == 2
        # Fused scores should be equal if ranks are flipped
        assert page.items[0].score == page.items[1].score
        assert "keyword" in page.items[0].matched_by
        assert "vector" in page.items[0].matched_by

@pytest.mark.asyncio
async def test_vector_channel_integration(search_service, vector_service):
    # This tests the call chain in _vector_channel
    with patch("src.core.registry.ServiceRegistry.get") as mock_get, \
         patch.object(CLIPProcessor, "encode_text") as mock_encode:
        
        mock_get.return_value = vector_service
        mock_encode.return_value = [0.1] * 512
        
        # Mock qdrant search results
        mock_result = MagicMock()
        mock_result.payload = {"asset_id": "mock_id"}
        vector_service.search = AsyncMock(return_value=[mock_result])
        
        request = SearchRequest(query="test", filter=AssetFilter(owner_id=PydanticObjectId()))
        hits = await search_service._vector_channel(request)
        
        assert hits == ["mock_id"]
        vector_service.search.assert_called_once()
