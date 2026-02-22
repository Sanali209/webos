from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from beanie import PydanticObjectId
from datetime import datetime

class DateRangeFilter(BaseModel):
    gte: Optional[datetime] = None
    lte: Optional[datetime] = None

class AssetFilter(BaseModel):
    """
    Unified filtering logic for MongoDB and Qdrant.
    """
    asset_types: Optional[List[str]] = None
    owner_id: Optional[PydanticObjectId] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    visibility: Optional[str] = "private"
    created_at: Optional[DateRangeFilter] = None
    
    def to_mongo_query(self) -> Dict[str, Any]:
        """
        Converts filters to a MongoDB match dictionary.
        """
        query = {}
        if self.asset_types:
            query["asset_types"] = {"$in": self.asset_types}
        if self.owner_id:
            query["owner_id"] = self.owner_id
        if self.tags:
            query["tags"] = {"$in": self.tags}
        if self.status:
            query["status"] = self.status
        if self.visibility:
            query["visibility"] = self.visibility
        
        if self.created_at:
            date_query = {}
            if self.created_at.gte:
                date_query["$gte"] = self.created_at.gte
            if self.created_at.lte:
                date_query["$lte"] = self.created_at.lte
            if date_query:
                query["created_at"] = date_query
                
        return query

class SearchRequest(BaseModel):
    query: Optional[str] = None
    filter: AssetFilter = Field(default_factory=AssetFilter)
    limit: int = 50
    cursor: Optional[str] = None  # Base64 encoded (score, id)
    include_facets: bool = False

class SearchHit(BaseModel):
    asset_id: str
    score: float
    matched_by: List[str] = [] # ["keyword", "vector", "graph"]
    # We can include a snippet of the asset here if needed
    
class FacetBucket(BaseModel):
    key: str
    count: int

class SearchFacets(BaseModel):
    asset_types: List[FacetBucket] = []
    tags: List[FacetBucket] = []
    detected_objects: List[FacetBucket] = []

class SearchPage(BaseModel):
    items: List[SearchHit]
    facets: Optional[SearchFacets] = None
    total_estimate: int = 0
    next_cursor: Optional[str] = None
