from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TaskItem(BaseModel):
    """Domain Entity for a Task."""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    is_completed: bool = False
    due_date: Optional[datetime] = None
