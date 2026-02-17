from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, Any

class CoreDocument(Document):
    """Base Beanie document for all engine modules.
    Provides standardized metadata fields.
    """
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1

    class Settings:
        name = "core_base" # Default name, should be overridden in subclasses
        use_revision = True

class SettingDocument(CoreDocument):
    """Beanie model for system and user settings."""
    key: str
    value: Any
    scope: str = "global"

    class Settings:
        name = "settings"
        indexes = ["key", "scope"]
