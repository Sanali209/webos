from typing import Dict, List, Optional
from loguru import logger
from src.modules.dam.schemas.asset_type import AssetTypeDefinition, GenericAssetType

class AssetTypeRegistry:
    """
    Open registry for asset types. 
    Modules register their own types via the `register_asset_types` hook.
    """
    
    def __init__(self):
        self._types: Dict[str, AssetTypeDefinition] = {}
        self._fallback = GenericAssetType()

    def register(self, definition: AssetTypeDefinition) -> None:
        if definition.type_id in self._types:
            logger.warning(f"Asset type '{definition.type_id}' is already registered. Skipping duplicate.")
            return
        self._types[definition.type_id] = definition

    def get_handler(self, mime: str) -> AssetTypeDefinition:
        """Auto-detect asset type from MIME type. Falls back to GenericAssetType."""
        for defn in self._types.values():
            if defn.can_handle(mime):
                return defn
        return self._fallback

    def all_types(self) -> List[AssetTypeDefinition]:
        return list(self._types.values()) + [self._fallback]

# Global Singleton
asset_type_registry = AssetTypeRegistry()
