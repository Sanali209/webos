import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock
from beanie import PydanticObjectId
from src.modules.dam.models import Asset
from src.modules.dam.drivers.image_driver import ImageDriver
from src.modules.dam.drivers.audio_driver import AudioDriver
from src.modules.dam.drivers.document_driver import DocumentDriver

@pytest.fixture
def dummy_asset():
    asset = MagicMock(spec=Asset)
    asset.filename = "test.file"
    asset.mime_type = "application/octet-stream"
    asset.metadata = {}
    return asset

@pytest.mark.asyncio
async def test_image_driver_corrupt(tmp_path, dummy_asset):
    # Create an invalid image
    img_path = tmp_path / "corrupt.jpg"
    img_path.write_bytes(b"not an image")
    
    driver = ImageDriver()
    assert driver.type_id == "image"
    
    # Run in event loop thread emulator
    metadata = await asyncio.to_thread(driver.extract_metadata, dummy_asset, img_path)
    assert "error" in metadata

@pytest.mark.asyncio
async def test_audio_driver_corrupt(tmp_path, dummy_asset):
    # Create invalid mp3
    audio_path = tmp_path / "corrupt.mp3"
    audio_path.write_bytes(b"not audio")
    
    driver = AudioDriver()
    assert driver.type_id == "audio"
    
    metadata = await asyncio.to_thread(driver.extract_metadata, dummy_asset, audio_path)
    # Should catch gracefully and return error dict 
    assert metadata == {} or "error" in metadata

@pytest.mark.asyncio
async def test_document_driver_txt(tmp_path, dummy_asset):
    # Create simple text file simulating generic document ingest 
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("hello world from testing")
    
    driver = DocumentDriver()
    assert driver.type_id == "document"
    
    metadata = await asyncio.to_thread(driver.extract_metadata, dummy_asset, txt_path)
    assert metadata["word_count_estimate"] == 4
