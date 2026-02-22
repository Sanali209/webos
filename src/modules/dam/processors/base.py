from typing import List, Protocol, runtime_checkable
from src.modules.dam.models import Asset

@runtime_checkable
class BasePipelineProcessor(Protocol):
    """
    Protocol for AI enrichment processors.
    """
    
    @property
    def name(self) -> str:
        """Unique identifier for the processor."""
        ...

    @property
    def applies_to(self) -> List[str]:
        """List of asset type IDs this processor handles."""
        ...

    async def process(self, asset: Asset) -> None:
        """
        Executes the enrichment logic.
        Updates the asset in-place.
        """
        ...
