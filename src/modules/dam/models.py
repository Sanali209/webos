from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from beanie import PydanticObjectId

from src.core.models import CoreDocument, OwnedDocument

class AssetStatus(str, Enum):
    PENDING    = "pending"
    UPLOADING  = "uploading"
    PROCESSING = "processing"
    READY      = "ready"
    MISSING    = "missing"
    ERROR      = "error"
    PARTIAL    = "partial"

class DetectedObject(BaseModel):
    class_name: str
    subclass: Optional[str] = None
    confidence: float
    bbox_x: float
    bbox_y: float
    bbox_w: float
    bbox_h: float
    model_name: Optional[str] = None

class Asset(OwnedDocument):
    """
    Primary Digital Asset entity.
    """
    filename:      str
    size:          Optional[int]   = None
    mime_type:     Optional[str]   = None
    asset_types:   List[str]       = ["other"]
    status:        AssetStatus     = AssetStatus.UPLOADING
    error_message: Optional[str]   = None
    visibility:    str             = "private"
    
    storage_urn: str
    
    hash:  Optional[str] = None
    phash: Optional[str] = None
    
    thumbnails: Dict[str, str] = {}
    width:    Optional[int]   = None
    height:   Optional[int]   = None
    duration: Optional[float] = None
    
    title:       Optional[str] = None
    description: Optional[str] = None
    tags:        List[str]     = []
    
    ai_caption:       Optional[str]  = None
    ai_tags:          List[str]      = []
    ai_confidence:    Dict[str, float] = {}
    
    detected_objects: List[DetectedObject] = []
    
    vectors_indexed:  Dict[str, bool] = {}
    vectors: Dict[str, List[float]] = {}
    
    metadata: Dict[str, Any] = {}
    
    version: int = 1

    @property
    def primary_type(self) -> str:
        return self.asset_types[0] if self.asset_types else "other"

    class Settings:
        name = "dam_assets"
        indexes = [
            [("asset_types", 1)],
            [("status", 1)],
            [("hash", 1)],
            [("storage_urn", 1)],
            [("tags", 1)],
            [("ai_tags", 1)],
            [("detected_objects.class_name", 1)],
            [("detected_objects.subclass", 1)],
            [("filename", "text"), ("title", "text"), ("description", "text"),
             ("tags", "text"), ("ai_tags", "text"), ("ai_caption", "text")],
        ]

class Link(CoreDocument):
    """
    Directed edge in the Knowledge Graph: Source -[relation]-> Target.
    """
    source_id:   PydanticObjectId
    target_id:   PydanticObjectId
    relation:    str
    weight:      float = 1.0
    metadata:    Dict[str, Any] = {}

    class Settings:
        name = "dam_links"
        indexes = [
            [("source_id", 1), ("relation", 1)],
            [("target_id", 1), ("relation", 1)],
        ]

class Album(OwnedDocument):
    """
    Virtual collection referencing assets via Links.
    """
    title:       str
    description: Optional[str] = None
    parent_id:   Optional[PydanticObjectId] = None
    cover_asset_id: Optional[PydanticObjectId] = None
    asset_ids: List[PydanticObjectId] = []

    class Settings:
        name = "dam_albums"
