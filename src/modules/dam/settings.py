from pydantic import BaseModel
from typing import Optional, List

class DAMSettings(BaseModel):
    """
    Settings schema for the DAM Module.
    """
    thumbnail_sizes: List[int] = [200, 800, 1920]
    cache_dir: str = "data/dam_cache"
    watch_paths: List[str] = []
    system_owner_id: str = "system"
