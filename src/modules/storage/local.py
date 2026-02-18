import os
import shutil
import aiofiles
from typing import List, BinaryIO
from src.core.storage import DataSource, FileMetadata

class LocalDataSource(DataSource):
    """
    Storage backend using the local filesystem.
    """
    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        os.makedirs(self.root_dir, exist_ok=True)

    async def connect(self) -> None:
        # Local filesystem doesn't need a connection
        pass

    def _get_abs_path(self, path: str) -> str:
        # Prevent path traversal
        normalized = os.path.normpath(os.path.join(self.root_dir, path.lstrip("/")))
        if not normalized.startswith(self.root_dir):
            raise ValueError(f"Path traversal attempt: {path}")
        return normalized

    async def list_dir(self, path: str) -> List[FileMetadata]:
        abs_path = self._get_abs_path(path)
        if not os.path.exists(abs_path):
            return []
        
        results = []
        for entry in os.scandir(abs_path):
            stat = entry.stat()
            results.append(FileMetadata(
                name=entry.name,
                path=os.path.relpath(entry.path, self.root_dir).replace("\\", "/"),
                size=stat.st_size,
                is_dir=entry.is_dir(),
                modified_at=stat.st_mtime
            ))
        return results

    async def open_file(self, path: str, mode: str = "rb") -> BinaryIO:
        abs_path = self._get_abs_path(path)
        # aiofiles returns an async file object, but the protocol expects a BinaryIO for simplicity in some contexts.
        # However, for true async we should use aiofiles.
        # Let's stick to standard open for now or specify protocol returns async-compatible objects.
        # actually nicegui/fastapi often want standard file handles.
        return open(abs_path, mode)

    async def save_file(self, path: str, content: bytes) -> None:
        abs_path = self._get_abs_path(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        async with aiofiles.open(abs_path, mode="wb") as f:
            await f.write(content)
