from datetime import datetime
from enum import Enum
from typing import Optional
from beanie import Document
from pydantic import BaseModel, Field
from src.core.models import CoreDocument

class ItemCategory(str, Enum):
    ELECTRONICS = "Electronics"
    FURNITURE = "Furniture"
    OFFICE = "Office Supplies"
    PERIPHERALS = "Peripherals"

class InventoryItem(CoreDocument):
    """
    Demonstrates a flat list with various data types.
    """
    name: str = Field(..., description="Item Name")
    category: ItemCategory = Field(..., description="Category")
    quantity: int = Field(0, description="Stock Qty")
    price: float = Field(0.0, description="Unit Price")
    is_active: bool = Field(True, description="Active Listing")
    last_audit: datetime = Field(default_factory=datetime.utcnow, description="Last Audit Date")

    class Settings:
        name = "demo_inventory_items"

class OrgNode(CoreDocument):
    """
    Demonstrates Hierarchical (Tree) Data.
    """
    name: str = Field(..., description="Employee/Dept Name")
    role: str = Field(..., description="Job Title")
    path: str = Field(..., description="Hierarchy Path (e.g., Board/CEO/CTO)")
    budget: int = Field(0, description="Department Budget")
    
    class Settings:
        name = "demo_org_nodes"
