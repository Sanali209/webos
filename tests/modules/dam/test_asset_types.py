import pytest
from src.modules.dam.schemas.asset_type import GenericAssetType
from src.modules.dam.services.builtin_types import (
    ImageAssetType, VideoAssetType, AudioAssetType, DocumentAssetType, UrlAssetType
)
from src.modules.dam.services.type_registry import AssetTypeRegistry

def test_image_type():
    t = ImageAssetType()
    assert t.type_id == "image"
    assert t.can_handle("image/jpeg") is True
    assert t.can_handle("image/png") is True
    assert t.can_handle("video/mp4") is False

def test_video_type():
    t = VideoAssetType()
    assert t.type_id == "video"
    assert t.can_handle("video/mp4") is True
    assert t.can_handle("video/quicktime") is True
    assert t.can_handle("image/png") is False

def test_document_type():
    t = DocumentAssetType()
    assert t.type_id == "document"
    assert t.can_handle("application/pdf") is True
    assert t.can_handle("text/plain") is True
    assert t.can_handle("application/msword") is True
    assert t.can_handle("image/jpeg") is False

def test_generic_fallback_type():
    t = GenericAssetType()
    assert t.type_id == "other"
    assert t.can_handle("application/octet-stream") is True
    assert t.can_handle("foo/bar") is True

def test_registry_resolution():
    registry = AssetTypeRegistry()
    registry.register(ImageAssetType())
    registry.register(VideoAssetType())
    
    # Resolves appropriately
    assert registry.get_handler("image/png").type_id == "image"
    assert registry.get_handler("video/webm").type_id == "video"
    
    # Fallback appropriately
    assert registry.get_handler("application/pdf").type_id == "other"
    assert registry.get_handler("").type_id == "other"

def test_all_types():
    registry = AssetTypeRegistry()
    registry.register(ImageAssetType())
    assert len(registry.all_types()) == 2 # Image + Generic
