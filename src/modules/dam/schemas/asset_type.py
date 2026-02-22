from abc import ABC, abstractmethod
from typing import List

class AssetTypeDefinition(ABC):
    """
    Base definition mapping MIME prefixes to a classification.
    Drives thumbnail strategies and pipeline exclusion logic.
    """
    
    @property
    @abstractmethod
    def type_id(self) -> str:
        """Unique categorical string ID, eg: 'image', 'video'"""
        pass
        
    @property
    @abstractmethod
    def accepted_mimes(self) -> List[str]:
        """List of exact MIME prefixes this definition handles, eg: ['image/', 'video/mp4']"""
        pass
        
    def can_handle(self, mime: str) -> bool:
        """
        Evaluates if the string mime matches one of the accepted prefixes.
        """
        if not mime:
            return False
            
        for prefix in self.accepted_mimes:
            if mime.startswith(prefix):
                return True
        return False
        
    def describe(self) -> str:
        """Human-readable schema label for the UI APIs."""
        return self.type_id.capitalize()

class GenericAssetType(AssetTypeDefinition):
    """Fallback handler mapping any unmatched types safely."""
    
    @property
    def type_id(self) -> str:
        return "other"
        
    @property
    def accepted_mimes(self) -> List[str]:
        return []
        
    def can_handle(self, mime: str) -> bool:
        # Fallback catches everything
        return True
