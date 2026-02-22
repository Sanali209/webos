import pytest
import asyncio
from typing import AsyncGenerator
from pathlib import Path
from beanie import PydanticObjectId, init_beanie
from mongomock_motor import AsyncMongoMockClient

from src.modules.dam.models import Asset, AssetStatus, Link, Album
from src.modules.dam.services.asset_service import AssetService
from src.modules.dam.services.builtin_types import ImageAssetType
from src.modules.dam.services.type_registry import asset_type_registry
from src.core.event_bus import event_bus

@pytest.fixture(autouse=True)
async def mock_db():
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client.get_database("test_db"),
        document_models=[Asset, Link, Album]
    )
    # Ensure types exist for valid mapping bounds 
    asset_type_registry.register(ImageAssetType())

@pytest.fixture
def test_file_path(tmp_path) -> Path:
    file_path = tmp_path / "test_image.png"
    file_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR" + b"A" * 100)
    return file_path

@pytest.fixture
def asset_service() -> AssetService:
    return AssetService()

@pytest.mark.asyncio
async def test_asset_registration_idempotence(test_file_path, asset_service):
    """Verifies duplicate ingestions resolve to the underlying hashed UUID bounds returning cleanly."""
    owner_id = PydanticObjectId()
    events = []
    
    async def trap(envelope):
        events.append(envelope.payload)
    event_bus.subscribe("dam:asset:ingested", trap)
    
    # Run 1: Create
    asset_1 = await asset_service.register_path(test_file_path, owner_id)
    assert asset_1.filename == "test_image.png"
    assert asset_1.status == AssetStatus.PROCESSING
    
    await asyncio.sleep(0.01)
    assert len(events) == 1
    assert events[0] == asset_1.id
    
    # Run 2: Dedup
    asset_2 = await asset_service.register_path(test_file_path, owner_id)
    assert asset_2.id == asset_1.id
    
    # No new event
    await asyncio.sleep(0.01)
    assert len(events) == 1

@pytest.mark.asyncio
async def test_asset_mark_missing(test_file_path, asset_service):
    owner_id = PydanticObjectId()
    
    asset = await asset_service.register_path(test_file_path, owner_id)
    assert asset.status == AssetStatus.PROCESSING

    await asset_service.mark_missing(test_file_path)
    
    reloaded = await Asset.get(asset.id)
    assert reloaded.status == AssetStatus.MISSING
