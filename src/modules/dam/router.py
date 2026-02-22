from fastapi import APIRouter, UploadFile, File, HTTPException, Response, Query
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Dict, Any, Optional
from beanie.odm.fields import PydanticObjectId
from pathlib import Path
import os
import asyncio

from src.core.registry import ServiceRegistry
from src.core.services.settings_service import settings_service
from src.modules.dam.models import Asset, AssetStatus, Album, Link
from src.modules.dam.services.asset_service import AssetService
from src.modules.dam.services.unified_search import UnifiedSearchService
from src.modules.dam.services.type_registry import asset_type_registry
from src.modules.dam.schemas.search import SearchRequest, SearchPage
from src.modules.dam.schemas.api import (
    AssetResponse, AssetUpdate, PipelineStatus,
    AlbumResponse, AlbumCreate, LinkResponse
)
from src.modules.dam.settings import DAMSettings

router = APIRouter(prefix="/dam", tags=["dam"])

def get_settings() -> DAMSettings:
    return settings_service.get_typed("dam", DAMSettings)

@router.get("/types", response_model=List[Dict[str, Any]])
async def get_asset_types():
    """
    Returns all registered asset types and their descriptions.
    Used by the UI to render type filters and badges.
    """
    types = asset_type_registry.all_types()
    return [{"id": t.type_id, "label": t.describe()} for t in types]

@router.post("/assets", response_model=AssetResponse, status_code=201)
async def upload_asset(file: UploadFile = File(...)):
    """
    Uploads a new file to the DAM.
    """
    content = await file.read()
    service = ServiceRegistry.get(AssetService)
    settings = get_settings()
    
    # In a real app, we'd get the actual user ID from auth
    # For now, we use the configured system owner
    owner_id = settings.system_owner_id
    
    asset = await service.ingest(
        file_bytes=content,
        filename=file.filename,
        owner_id=owner_id
    )
    return AssetResponse.from_asset(asset)

@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
    skip: int = 0, 
    limit: int = 50, 
    type: Optional[str] = None,
    status: Optional[str] = None
):
    """
    Lists assets with optional filtering.
    """
    query = {}
    if type:
        query["primary_type"] = type
    if status:
        query["status"] = status
        
    assets = await Asset.find(query).skip(skip).limit(limit).sort("-created_at").to_list()
    return [AssetResponse.from_asset(a) for a in assets]

@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str):
    """
    Returns detailed metadata for a single asset.
    """
    asset = await Asset.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetResponse.from_asset(asset)

@router.patch("/assets/{asset_id}", response_model=AssetResponse)
async def update_asset(asset_id: str, update: AssetUpdate):
    """
    Updates mutable metadata fields of an asset.
    """
    asset = await Asset.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    if update.title is not None:
        asset.title = update.title
    if update.description is not None:
        asset.description = update.description
    if update.tags is not None:
        asset.tags = update.tags
    if update.visibility is not None:
        asset.visibility = update.visibility
        
    await asset.save()
    return AssetResponse.from_asset(asset)

@router.delete("/assets/{asset_id}", status_code=204)
async def delete_asset(asset_id: str):
    """
    Permanently deletes an asset and its derivatives.
    """
    service = ServiceRegistry.get(AssetService)
    await service.delete(asset_id)
    return Response(status_code=204)

@router.get("/assets/{asset_id}/thumbnail/{size}.webp")
async def get_thumbnail(asset_id: str, size: int):
    """
    Returns a cached thumbnail image.
    """
    settings = get_settings()
    thumb_path = Path(settings.cache_dir) / asset_id / f"{size}.webp"
    
    if not thumb_path.exists():
        # Fallback to a placeholder if it doesn't exist yet
        # In a real app, we might trigger generation here or return 404
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    return FileResponse(
        thumb_path, 
        media_type="image/webp",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@router.get("/assets/{asset_id}/download")
async def download_asset(asset_id: str):
    """
    Streams the original asset binary from storage.
    """
    asset = await Asset.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    from src.core.storage import storage_manager
    try:
        # Resolve URN and open stream via AFS
        file_io = await storage_manager.open_file(asset.storage_urn)
        
        async def file_generator():
            try:
                # Read in 1MB chunks
                while chunk := file_io.read(1024 * 1024):
                    yield chunk
            finally:
                if hasattr(file_io, "close"):
                    # Check if close is sync or async
                    if asyncio.iscoroutinefunction(file_io.close):
                        await file_io.close()
                    else:
                        file_io.close()

        return StreamingResponse(
            file_generator(),
            media_type=asset.mime_type or "application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{asset.filename}"',
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")

@router.get("/assets/{asset_id}/links", response_model=List[LinkResponse])
async def get_asset_links(asset_id: str):
    """
    Returns all relationships (links) for a given asset.
    """
    links = await Link.find({
        "$or": [
            {"source_id": PydanticObjectId(asset_id)},
            {"target_id": PydanticObjectId(asset_id)}
        ]
    }).to_list()
    
    return [
        LinkResponse(
            source_id=str(l.source_id),
            target_id=str(l.target_id),
            relation=l.relation,
            weight=l.weight,
            metadata=l.metadata
        ) for l in links
    ]

# --- Album Endpoints ---

@router.post("/albums", response_model=AlbumResponse, status_code=201)
async def create_album(create: AlbumCreate):
    """
    Creates a new virtual collection.
    """
    settings = get_settings()
    owner_id = settings.system_owner_id
    
    album = Album(
        title=create.title,
        description=create.description,
        owner_id=owner_id
    )
    await album.insert()
    return AlbumResponse.from_album(album)

@router.get("/albums", response_model=List[AlbumResponse])
async def list_albums():
    """
    Lists all albums the current user can access.
    """
    albums = await Album.find_all().to_list()
    return [AlbumResponse.from_album(a) for a in albums]

@router.get("/albums/{album_id}", response_model=AlbumResponse)
async def get_album(album_id: str):
    """
    Returns album details.
    """
    album = await Album.get(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    return AlbumResponse.from_album(album)

@router.post("/albums/{album_id}/assets/{asset_id}", status_code=200)
async def add_asset_to_album(album_id: str, asset_id: str):
    """
    Adds an asset to an album.
    """
    album = await Album.get(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    aid = PydanticObjectId(asset_id)
    if aid not in album.asset_ids:
        album.asset_ids.append(aid)
        await album.save()
        
    return {"status": "success"}

@router.delete("/albums/{album_id}/assets/{asset_id}", status_code=200)
async def remove_asset_from_album(album_id: str, asset_id: str):
    """
    Removes an asset from an album.
    """
    album = await Album.get(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    aid = PydanticObjectId(asset_id)
    if aid in album.asset_ids:
        album.asset_ids.remove(aid)
        await album.save()
        
    return {"status": "success"}

@router.post("/search", response_model=SearchPage)
async def search_assets(request: SearchRequest):
    """
    Executes a hybrid search across keyword and vector channels.
    """
    service = ServiceRegistry.get(UnifiedSearchService)
    return await service.search(request)

@router.get("/pipeline/status", response_model=PipelineStatus)
async def get_pipeline_status():
    """
    Returns an overview of the processing pipeline health.
    """
    total = await Asset.count()
    pending = await Asset.find(Asset.status == AssetStatus.PENDING).count()
    processing = await Asset.find(Asset.status == AssetStatus.PROCESSING).count()
    ready = await Asset.find(Asset.status == AssetStatus.READY).count()
    error = await Asset.find(Asset.status == AssetStatus.ERROR).count()
    
    # Coverage calculation (simplified: percentage of READY vs PENDING/PROCESSING)
    coverage = (ready / total * 100) if total > 0 else 0.0
    
    return PipelineStatus(
        total=total,
        pending=pending,
        processing=processing,
        ready=ready,
        error=error,
        vector_coverage=coverage
    )
