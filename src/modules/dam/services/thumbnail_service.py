import asyncio
from typing import Dict
from pathlib import Path
from PIL import Image, ImageOps
from loguru import logger
from src.modules.dam.models import Asset
from src.core.storage import storage_manager

class ThumbnailGenerator:
    def __init__(self, cache_dir: str, sizes: list[int]):
        self.cache_root = Path(cache_dir)
        self.sizes = sizes
        
        # Ensure root structure exists natively avoiding I/O misses
        self.cache_root.mkdir(parents=True, exist_ok=True)

    async def generate(self, asset: Asset) -> Dict[str, str]:
        """
        Creates WEBP thumbnails handling orientation states robustly.
        Listens to `dam:asset:ingested` natively.
        """
        # Skip gracefully if no visual dimension maps directly (e.g text/audio)
        if "image" not in asset.asset_types and "video" not in asset.asset_types:
            logger.debug(f"ThumbnailGenerator skipping unsupported type {asset.primary_type} for {asset.id}")
            return {}

        out_thumbs = {}
        
        # Determine internal resolution boundaries mapping against real AFS structures 
        if not asset.storage_urn.startswith("fs://local/"):
            # Mock or ignore complex S3 bucket downloads purely for initial cache generation bounds
            return {}

        source_path = Path(asset.storage_urn.replace("fs://local/", ""))
        if not source_path.exists():
            return {}

        asset_hash = asset.hash
        if not asset_hash:
            return {}
            
        for size in self.sizes:
            # Layout -> cache_root/1a/1a2b3c.../200.webp
            target_path = self.cache_root / asset_hash[:2] / asset_hash / f"{size}.webp"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            if "video" in asset.asset_types:
                # Fallback to pure path placeholder until ffmpeg explicitly is mapped
                pass
            else:
                try:
                    await asyncio.to_thread(self._resize_image, source_path, target_path, size)
                except Exception as e:
                    logger.warning(f"ThumbnailGenerator failed to build {size}px map for {asset.id}: {e}")
                    asset.status = "error"
                    asset.error_message = "Thumbnail generation failed"
                    await asset.save()
                    return {}
            
            # Form final namespace tracking pointer
            out_thumbs[str(size)] = f"fs://cache/dam/{target_path.relative_to(self.cache_root).as_posix()}"

        # Inject references and commit updates 
        asset.thumbnails = out_thumbs
        await asset.save()
        return out_thumbs

    def _resize_image(self, src: Path, dst: Path, max_px: int) -> None:
        """Runs within a threaded executor resolving CPU bounds securely."""
        with Image.open(src) as img:
            img = ImageOps.exif_transpose(img)
            img.thumbnail((max_px, max_px), Image.Resampling.LANCZOS)
            # Commit first frame purely resolving animated boundaries correctly 
            img.save(dst, "WEBP", quality=85)
