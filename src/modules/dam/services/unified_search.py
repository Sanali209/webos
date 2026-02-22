import asyncio
import base64
import json
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger
from beanie import PydanticObjectId

from src.modules.dam.models import Asset
from src.modules.dam.schemas.search import (
    SearchRequest, SearchPage, SearchHit, SearchFacets, FacetBucket, AssetFilter
)
from src.modules.dam.services.vector_service import VectorService
from src.modules.dam.processors.clip_processor import CLIPProcessor
from src.core.registry import ServiceRegistry

class UnifiedSearchService:
    """
    Fuses Keyword (Mongo) and Vector (Qdrant) search results using RRF.
    """
    
    def __init__(self, k: int = 60):
        self.k = k  # RRF constant

    async def search(self, request: SearchRequest) -> SearchPage:
        """
        Executes hybrid search and returns a paginated page.
        """
        # 1. Parallel Channel Execution
        tasks = []
        if request.query:
            tasks.append(self._keyword_channel(request))
            tasks.append(self._vector_channel(request))
        else:
            # Simple filtered list if no query
            return await self._list_filtered(request)

        results = await asyncio.gather(*tasks)
        keyword_hits = results[0]
        vector_hits = results[1]

        # 1.1 Graph Expansion Channel
        # We take the top 10 from each primary channel and find their neighbors
        seeds = list(set(keyword_hits[:10] + vector_hits[:10]))
        graph_hits = await self._graph_extension_channel(seeds) if seeds else []

        # 2. Reciprocal Rank Fusion (RRF)
        fused_scores: Dict[str, float] = {}
        matched_by: Dict[str, List[str]] = {}

        def apply_rrf(hits: List[str], source: str):
            for rank, asset_id in enumerate(hits):
                score = 1.0 / (self.k + rank + 1)
                fused_scores[asset_id] = fused_scores.get(asset_id, 0.0) + score
                if asset_id not in matched_by:
                    matched_by[asset_id] = []
                matched_by[asset_id].append(source)

        apply_rrf(keyword_hits, "keyword")
        apply_rrf(vector_hits, "vector")
        apply_rrf(graph_hits, "graph")

        # 3. Sorting & Pagination
        sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
        
        # Simple slicing for now (cursor logic can be added later)
        start = 0
        end = start + request.limit
        page_ids = sorted_ids[start:end]

        hits = [
            SearchHit(
                asset_id=aid, 
                score=fused_scores[aid], 
                matched_by=matched_by[aid]
            ) for aid in page_ids
        ]

        # 4. Facets (Optional)
        facets = None
        if request.include_facets:
            facets = await self._compute_facets(request.filter)

        return SearchPage(
            items=hits,
            facets=facets,
            total_estimate=len(sorted_ids)
        )

    async def _keyword_channel(self, request: SearchRequest) -> List[str]:
        """
        MongoDB Text Search Channel.
        """
        query = request.filter.to_mongo_query()
        query["$text"] = {"$search": request.query}
        
        # We only need the IDs
        cursor = Asset.find(query).project({"_id": 1})
        cursor.sort([("score", {"$meta": "textScore"})])
        
        hits = await cursor.limit(request.limit * 2).to_list()
        return [str(h.id) for h in hits]

    async def _vector_channel(self, request: SearchRequest) -> List[str]:
        """
        Qdrant Vector Search Channel.
        """
        vs = ServiceRegistry.get(VectorService)
        if not vs.is_available:
            return []

        try:
            # 1. Encode query text
            processor = CLIPProcessor() # Using singleton eventually
            query_vector = processor.encode_text(request.query)
            
            # 2. Search Qdrant
            # We pass owner_id filter to Qdrant directly for performance
            results = await vs.search(
                vector_name="clip",
                query_vector=query_vector,
                limit=request.limit * 2,
                owner_id=request.filter.owner_id
            )
            return [r.payload["asset_id"] for r in results]
        except Exception as e:
            logger.error(f"UnifiedSearchService: Vector channel failed: {e}")
            return []

    async def _graph_extension_channel(self, seed_ids: List[str]) -> List[str]:
        """
        Finds assets linked to the primary hits via the Knowledge Graph.
        """
        from src.modules.dam.models import Link
        
        seeds = [PydanticObjectId(sid) for sid in seed_ids]
        
        # Find links where these seeds are either source or target
        links = await Link.find({
            "$or": [
                {"source_id": {"$in": seeds}},
                {"target_id": {"$in": seeds}}
            ]
        }).to_list()
        
        # Extract the neighbors
        neighbor_ids = set()
        for link in links:
            if str(link.source_id) in seed_ids:
                neighbor_ids.add(str(link.target_id))
            else:
                neighbor_ids.add(str(link.source_id))
        
        # Filter out self (seed_ids)
        neighbor_ids = neighbor_ids - set(seed_ids)
        
        return list(neighbor_ids)

    async def _list_filtered(self, request: SearchRequest) -> SearchPage:
        """
        Fallback for when no query string is provided.
        """
        query = request.filter.to_mongo_query()
        cursor = Asset.find(query).sort("-created_at")
        
        hits = await cursor.limit(request.limit).to_list()
        items = [SearchHit(asset_id=str(h.id), score=1.0) for h in hits]
        
        facets = None
        if request.include_facets:
            facets = await self._compute_facets(request.filter)

        return SearchPage(
            items=items,
            facets=facets,
            total_estimate=await Asset.find(query).count()
        )

    async def _compute_facets(self, filter: AssetFilter) -> SearchFacets:
        """
        Aggregates counts for UI sidebars.
        """
        query = filter.to_mongo_query()
        
        async def get_buckets(field: str) -> List[FacetBucket]:
            try:
                # Standard Beanie aggregation on the Document class
                pipeline = [
                    {"$match": query},
                    {"$unwind": f"${field}"},
                    {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 10}
                ]
                results = await Asset.aggregate(pipeline).to_list()
                return [FacetBucket(key=str(r["_id"]), count=r["count"]) for r in results]
            except Exception as e:
                logger.error(f"UnifiedSearchService: Facets failed for {field}: {e}")
                return []

        types_task = get_buckets("asset_types")
        tags_task = get_buckets("tags")
        
        results = await asyncio.gather(types_task, tags_task)
        
        return SearchFacets(
            asset_types=results[0],
            tags=results[1]
        )
