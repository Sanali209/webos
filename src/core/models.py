from datetime import datetime
from typing import Optional, Type, TypeVar, Any, Dict
from uuid import UUID, uuid4

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


class AuditMixin(BaseModel):
    """
    Mixin for adding audit fields to models.
    """
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[PydanticObjectId] = None
    updated_by: Optional[PydanticObjectId] = None


class CoreDocument(Document, AuditMixin):
    """
    Base class for all WebOS documents.
    """
    class Settings:
        use_revision = True  # Enable optimistic locking


class OwnedDocument(CoreDocument):
    """
    Base class for documents owned by a specific user.
    Used for automated user isolation.
    """
    owner_id: PydanticObjectId = Field(description="ID of the user who owns this document")

    class Settings:
        # We can implement global filters here or in the service layer
        pass
