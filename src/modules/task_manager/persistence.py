from src.core.infrastructure.persistence.models import CoreDocument
from typing import Optional
from datetime import datetime

class TaskDocument(CoreDocument):
    """Beanie model for Task storage."""
    title: str
    description: Optional[str] = None
    is_completed: bool = False
    due_date: Optional[datetime] = None

    class Settings:
        name = "tasks"
