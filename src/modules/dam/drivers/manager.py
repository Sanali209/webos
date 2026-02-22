import asyncio
from pathlib import Path
from typing import Dict, Any
from src.modules.dam.models import Asset
from src.modules.dam.drivers.base import BaseAssetDriver
from loguru import logger

class AssetDriverManager:
    """
    Registry and dispatcher for asset drivers.
    Routes an asset to the appropriate driver based on its primary type.
    """
    
    def __init__(self):
        self._drivers: Dict[str, BaseAssetDriver] = {}

    def register(self, driver: BaseAssetDriver) -> None:
        if driver.type_id in self._drivers:
            logger.warning(f"Driver for type '{driver.type_id}' is already registered. Overwriting.")
        self._drivers[driver.type_id] = driver
        logger.debug(f"Registered Asset Driver: {driver.__class__.__name__} for type '{driver.type_id}'")

    async def process(self, asset: Asset, file_path: Path) -> None:
        """
        Processes an asset using its registered driver.
        Dispatches async using `asyncio.to_thread` for blocking extraction calls.
        """
        primary_type = asset.primary_type
        
        driver = self._drivers.get(primary_type)
        if not driver:
            logger.debug(f"AssetDriverManager: No driver registered for type '{primary_type}'. Skipped extraction.")
            return

        try:
            # Offload heavy IO/CPU blocking tasks onto the threadpool
            metadata = await asyncio.to_thread(driver.extract_metadata, asset, file_path)
            
            # Mount into Schema-on-Read namespace
            if metadata:
                asset.metadata[primary_type] = metadata
                
        except Exception as e:
            logger.error(f"AssetDriverManager failed processing asset {asset.id} with '{driver.__class__.__name__}': {str(e)}")
            asset.metadata[primary_type] = {"error": str(e)}
