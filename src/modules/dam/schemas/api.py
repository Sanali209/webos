from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from beanie import PydanticObjectId

class AssetResponse(BaseModel):
    id: str
    filename: str
    title: Optional[str] = None
    description: Optional[str] = None
    asset_types: List[str]
    primary_type: str
    tags: List[str]
    ai_tags: List[str] = []
    ai_caption: Optional[str] = None
    status: str
    visibility: str
    created_at: datetime
    updated_at: datetime
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    @classmethod
    def from_asset(cls, asset: Any) -> "AssetResponse":
        return cls(
            id=str(asset.id),
            filename=asset.filename,
            title=asset.title,
            description=asset.description,
            asset_types=asset.asset_types,
            primary_type=asset.primary_type,
            tags=asset.tags,
            ai_tags=asset.ai_tags,
            ai_caption=asset.ai_caption,
            status=asset.status,
            visibility=asset.visibility,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
            file_size=asset.size,
            mime_type=asset.mime_type,
            metadata=asset.metadata
        )

class AssetUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    visibility: Optional[str] = None

class PipelineStatus(BaseModel):
    total: int
    pending: int
    processing: int
    ready: int
    error: int
    vector_coverage: float # Percentage of assets with vectors

class AlbumResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    cover_asset_id: Optional[str] = None
    asset_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_album(cls, album: Any) -> "AlbumResponse":
        return cls(
            id=str(album.id),
            title=album.title,
            description=album.description,
            cover_asset_id=str(album.cover_asset_id) if album.cover_asset_id else None,
            asset_count=len(album.asset_ids),
            created_at=album.created_at,
            updated_at=album.updated_at
        )

class AlbumCreate(BaseModel):
    title: str
    description: Optional[str] = None

class LinkResponse(BaseModel):
    source_id: str
    target_id: str
    relation: str
    weight: float
    metadata: Dict[str, Any] = {}
