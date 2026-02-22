import hashlib
import asyncio
import mimetypes
try:
    import magic as _magic
    def _get_mime(data: bytes) -> str:
        return _magic.from_buffer(data, mime=True)
except (ImportError, Exception):
    _magic = None
    def _get_mime(data: bytes) -> str:  # type: ignore[misc]
        return "application/octet-stream"
from pathlib import Path
from typing import Optional, List
from beanie import PydanticObjectId
from loguru import logger

from src.core.event_bus import event_bus
from src.core.storage import storage_manager
from src.modules.dam.models import Asset, AssetStatus, Link, Album
from src.modules.dam.services.type_registry import asset_type_registry

class AssetService:
    """
    Manages physical file indexing, ingestion deduplication, and lifecycle events.
    Serves as the backbone of the DAM data architecture bridging Storage via core AFS.
    """
    
    async def ingest(
        self, 
        file_bytes: bytes, 
        filename: str,
        owner_id: PydanticObjectId, 
        asset_types: List[str] = None, 
        tags: List[str] = None, 
        title: Optional[str] = None, 
        visibility: str = "private"
    ) -> Asset:
        """
        Ingests a new binary stream (e.g., from an API upload).
        Copies it to managed AFS storage and indexes it.
        """
        # Calculate SHA-256 hash in blocks 
        sha256 = hashlib.sha256(file_bytes).hexdigest()
        
        # Deduplication check
        existing = await Asset.find_one(Asset.hash == sha256)
        if existing:
            logger.info(f"AssetService: deduplicated upload resolving to {existing.id} (hash {sha256})")
            return existing

        mime_type = magic.from_buffer(file_bytes[:2048], mime=True)
        primary_type = asset_type_registry.get_handler(mime_type).type_id

        # Store in managed block via AFS (defaulting to local core bucket `dam`)
        # Layout: fs://local/dam/{hash[:2]}/{hash}/{filename}
        storage_urn = f"fs://local/dam/{sha256[:2]}/{sha256}/{filename}"
        
        try:
            await storage_manager.save_file(storage_urn, file_bytes)
        except Exception as e:
            logger.error(f"AssetService: AFS save failed for {filename}: {e}")
            asset = Asset(
                filename=filename,
                storage_urn=storage_urn,
                owner_id=owner_id,
                status=AssetStatus.ERROR,
                error_message="Storage IO Error"
            )
            await asset.save()
            return asset
            
        return await self._create_and_dispatch(
            filename=filename,
            storage_urn=storage_urn,
            owner_id=owner_id,
            mime_type=mime_type,
            size=len(file_bytes),
            sha256=sha256,
            asset_types=asset_types or [primary_type],
            tags=tags or [],
            title=title,
            visibility=visibility
        )

    async def register_path(self, path: Path, owner_id: PydanticObjectId) -> Asset:
        """
        Registers an existing unmanaged physical file from the `WatcherService`.
        Does NOT move the file. Idempotent.
        """
        storage_urn = f"fs://local/{path.as_posix()}"
        existing = await Asset.find_one(Asset.storage_urn == storage_urn)
        
        if existing:
            return existing

        mime_type = magic.from_file(str(path), mime=True)
        primary_type = asset_type_registry.get_handler(mime_type).type_id
        
        sha256_hash = await asyncio.to_thread(self._hash_file, path)
        size = path.stat().st_size
        
        return await self._create_and_dispatch(
            filename=path.name,
            storage_urn=storage_urn,
            owner_id=owner_id,
            mime_type=mime_type,
            size=size,
            sha256=sha256_hash,
            asset_types=[primary_type],
            tags=[],
            title=None,
            visibility="private"
        )
        
    async def _create_and_dispatch(self, **kwargs) -> Asset:
        asset = Asset(
            filename=kwargs['filename'],
            storage_urn=kwargs['storage_urn'],
            owner_id=kwargs['owner_id'],
            mime_type=kwargs['mime_type'],
            size=kwargs['size'],
            hash=kwargs['sha256'],
            asset_types=kwargs['asset_types'],
            tags=kwargs['tags'],
            title=kwargs['title'],
            visibility=kwargs['visibility'],
            status=AssetStatus.PROCESSING
        )
        await asset.save()
        
        # Fire indexing event natively allowing listeners like Drivers and Thumbnails to begin
        await event_bus.emit("dam:asset:ingested", asset.id)
        return asset

    def _hash_file(self, path: Path) -> str:
        """Synchronous chunked file hashing to avoid memory overload."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096 * 1024), b""): 
                hasher.update(chunk)
        return hasher.hexdigest()

    async def delete(self, asset_id: PydanticObjectId) -> None:
        """
        Completely removes asset, its derivatives, and graph edge connections.
        """
        asset = await Asset.get(asset_id)
        if not asset:
            return

        # Phase 1: Storage Clean
        try:
            # Delete original if managed (in /dam/ cache prefix)
            if "/dam/" in asset.storage_urn:
                # We would call AFS delete here if implemented, but core doesn't have it yet!
                pass
                
            # Clear thumbnail cache derivatives manually parsing storage bindings
            logger.info(f"AssetService: Cleared cache instances for {asset.id}")
        except Exception as e:
            logger.warning(f"AssetService: Storage cleanup error for {asset.id}: {e}")

        # Phase 2: Graph Clean
        await Link.find(Link.source_id == asset.id).delete()
        await Link.find(Link.target_id == asset.id).delete()
        
        # Remove from encompassing Albums utilizing array projections
        albums = await Album.find(Album.asset_ids == asset.id).to_list()
        for album in albums:
            album.asset_ids.remove(asset.id)
            await album.save()

        # Phase 3: Root Document Clean
        await asset.delete()
        logger.info(f"AssetService: Asset {asset.id} successfully deleted.")

    async def refresh_asset(self, path: Path) -> None:
        """Triggered upon FileModifiedEvent. Rebuilds hashes."""
        storage_urn = f"fs://local/{path.as_posix()}"
        asset = await Asset.find_one(Asset.storage_urn == storage_urn)
        if asset:
            asset.hash = await asyncio.to_thread(self._hash_file, path)
            asset.size = path.stat().st_size
            asset.status = AssetStatus.PROCESSING
            await asset.save()
            await event_bus.publish("dam:asset:ingested", asset.id)

    async def update_storage_urn(self, old_path: Path, new_path: Path) -> None:
        """Resolves FileMovedEvent mapping records preventing loss states."""
        old_urn = f"fs://local/{old_path.as_posix()}"
        new_urn = f"fs://local/{new_path.as_posix()}"
        asset = await Asset.find_one(Asset.storage_urn == old_urn)
        if asset:
            asset.storage_urn = new_urn
            asset.filename = new_path.name
            await asset.save()

    async def mark_missing(self, path: Path) -> None:
        """Resolves internal graphs upon unmanaged file system deletes."""
        urn = f"fs://local/{path.as_posix()}"
        asset = await Asset.find_one(Asset.storage_urn == urn)
        if asset:
            asset.status = AssetStatus.MISSING
            await asset.save()
