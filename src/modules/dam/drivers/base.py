from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path
from src.modules.dam.models import Asset

class BaseAssetDriver(ABC):
    """
    Abstract base class for all Asset Drivers.
    Drivers are responsible for extracting technical metadata from files
    based on their asset type.
    """

    @property
    @abstractmethod
    def type_id(self) -> str:
        """
        The asset type this driver processes. Must match an AssetTypeDefinition.type_id.
        e.g., 'image', 'video', 'audio', 'document'
        """
        pass

    @abstractmethod
    def extract_metadata(self, asset: Asset, file_path: Path) -> Dict[str, Any]:
        """
        Extracts metadata from the given file natively.
        Runs in a background TaskIQ worker, allowing for blocking I/O calls.
        
        Args:
            asset: The Asset Beanie document (contains properties like mime_type).
            file_path: The absolute path to the local file to process.
            
        Returns:
            A dictionary containing the extracted metadata. This will be stored 
            under the namespace matching the `type_id` within `asset.metadata`.
        """
        pass
