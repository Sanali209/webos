from typing import List, Optional, Any, Dict
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from loguru import logger
from beanie import PydanticObjectId

from src.modules.dam.models import Asset

class VectorService:
    """
    Manages semantic search collections in Qdrant.
    """
    
    def __init__(self, url: str, api_key: Optional[str] = None):
        try:
            self.client = QdrantClient(url=url, api_key=api_key)
            self._available = True
        except Exception as e:
            logger.error(f"VectorService: Failed to connect to Qdrant at {url}: {e}")
            self._available = False
            
        self.COLLECTION_NAME = "dam_clip"
        self.VECTOR_NAME = "clip"
        self.DIMENSION = 512
        self.DISTANCE = models.Distance.COSINE

    @property
    def is_available(self) -> bool:
        return self._available

    async def ensure_collections(self):
        """
        Creates the standard DAM collection if it doesn't exist.
        """
        if not self._available:
            return

        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.COLLECTION_NAME for c in collections)
            
            if not exists:
                logger.info(f"VectorService: Creating collection '{self.COLLECTION_NAME}'...")
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config={
                        self.VECTOR_NAME: models.VectorParams(
                            size=self.DIMENSION,
                            distance=self.DISTANCE
                        )
                    }
                )
                
                # Create payload indexes for security/filtering
                self.client.create_payload_index(
                    collection_name=self.COLLECTION_NAME,
                    field_name="owner_id",
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
                self.client.create_payload_index(
                    collection_name=self.COLLECTION_NAME,
                    field_name="visibility",
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
        except Exception as e:
            logger.error(f"VectorService: Failed to ensure collection: {e}")
            self._available = False

    async def upsert_asset(self, asset: Asset, vector: List[float]):
        """
        Syncs an asset's embedding into Qdrant.
        """
        if not self._available:
            return

        try:
            # Qdrant Point ID must be a UUID or int. 
            # We use the Asset.id hex string which is a valid UUID-like format.
            point_id = str(asset.id)
            
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector={self.VECTOR_NAME: vector},
                        payload={
                            "asset_id": str(asset.id),
                            "owner_id": str(asset.owner_id),
                            "visibility": asset.visibility,
                            "filename": asset.filename,
                            "primary_type": asset.primary_type
                        }
                    )
                ]
            )
            
            # Update asset record
            asset.vectors[self.VECTOR_NAME] = vector
            asset.vectors_indexed[self.VECTOR_NAME] = True
            await asset.save()
            
        except Exception as e:
            logger.error(f"VectorService: Failed to upsert asset {asset.id}: {e}")

    async def delete_asset(self, asset_id: PydanticObjectId):
        """
        Removes an asset from Qdrant.
        """
        if not self._available:
            return

        try:
            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=models.PointIdsList(
                    points=[str(asset_id)]
                )
            )
        except Exception as e:
            logger.error(f"VectorService: Failed to delete asset {asset_id} from Qdrant: {e}")

    async def search(self, query_vector: List[float], limit: int = 20, owner_id: Optional[PydanticObjectId] = None) -> List[dict]:
        """
        Performs semantic similarity search.
        """
        if not self._available:
            return []

        try:
            # Build filters
            filter_conditions = []
            if owner_id:
                filter_conditions.append(
                    models.FieldCondition(
                        key="owner_id",
                        match=models.MatchValue(value=str(owner_id))
                    )
                )
            
            # OR visibility == "public" (If we decide to support public assets across owners)
            # For now, just strict ownership or simple search
            
            query_filter = models.Filter(must=filter_conditions) if filter_conditions else None
            
            results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=(self.VECTOR_NAME, query_vector),
                limit=limit,
                query_filter=query_filter,
                with_payload=True
            )
            
            return [hit.payload for hit in results]
        except Exception as e:
            logger.error(f"VectorService: Search failed: {e}")
            return []
