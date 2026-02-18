from typing import Protocol, List, Dict, Optional, BinaryIO
from abc import abstractmethod
from pydantic import BaseModel
import asyncio

class FileMetadata(BaseModel):
    """Standard metadata for files across different data sources."""
    name: str
    path: str
    size: int
    is_dir: bool
    modified_at: Optional[float] = None

class DataSource(Protocol):
    """Protocol for all storage backends (Local, S3, FTP, etc)."""
    @abstractmethod
    async def connect(self) -> None: ...
    
    @abstractmethod
    async def list_dir(self, path: str) -> List[FileMetadata]: ...
    
    @abstractmethod
    async def open_file(self, path: str, mode: str = "rb") -> BinaryIO: ...
    
    @abstractmethod
    async def save_file(self, path: str, content: bytes) -> None: ...

class AFSManager:
    """
    Abstract File System Manager.
    Resolves fs://<source_id>/<path> URNs to specific data sources.
    """
    def __init__(self):
        self._sources: Dict[str, DataSource] = {}

    def register_source(self, source_id: str, source: DataSource):
        """Register a storage backend."""
        self._sources[source_id] = source

    async def resolve(self, urn: str) -> tuple[DataSource, str]:
        """Resolves a URN to a (DataSource, relative_path) tuple."""
        if not urn.startswith("fs://"):
            raise ValueError(f"Invalid URN format: {urn}. Must start with fs://")
        
        parts = urn[5:].split("/", 1)
        source_id = parts[0]
        path = parts[1] if len(parts) > 1 else ""
        
        if source_id not in self._sources:
            raise KeyError(f"Storage source '{source_id}' not registered.")
        
        return self._sources[source_id], path

    async def list_dir(self, urn: str) -> List[FileMetadata]:
        source, path = await self.resolve(urn)
        return await source.list_dir(path)

    async def open_file(self, urn: str, mode: str = "rb") -> BinaryIO:
        source, path = await self.resolve(urn)
        return await source.open_file(path, mode)

    async def save_file(self, urn: str, content: bytes) -> None:
        source, path = await self.resolve(urn)
        await source.save_file(path, content)

# Global AFS Instance
afs = AFSManager()
storage_manager = afs
