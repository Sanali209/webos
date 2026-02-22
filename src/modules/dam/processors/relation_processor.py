import asyncio
import numpy as np
from typing import List, Optional, Any, Dict
from loguru import logger
from beanie import PydanticObjectId

from src.modules.dam.models import Asset, Link
from src.core.registry import ServiceRegistry

class VectorRelationProcessor:
    """
    Synthesizes multiple vector types (CLIP, BLIP, MobileNet) to create 
    intelligent relations between assets.
    """
    
    def __init__(self, top_k: int = 5, threshold: float = 0.85):
        self.top_k = top_k
        self.threshold = threshold
        self.applies_to = ["image"] # Extendable to video keyframes later

    @property
    def name(self) -> str:
        return "relation_analysis"

    async def process(self, asset: Asset) -> None:
        """
        Finds similar assets using weighted multi-vector similarity 
        and creates Link documents.
        """
        # 1. Check if we have the needed vectors
        required = ["clip", "blip", "mobilenet"]
        if not all(v in asset.vectors for v in required):
            logger.warning(f"RelationProcessor: Missing required vectors for {asset.id}. Required: {required}")
            return

        # 2. Query candidates from Qdrant (using CLIP as the primary filter for performance)
        from src.modules.dam.services.vector_service import VectorService
        vs = ServiceRegistry.get(VectorService)
        if not vs.is_available:
            logger.warning("RelationProcessor: VectorService unavailable, skipping relation analysis.")
            return

        # Get candidates (excluding self)
        candidates = await vs.search(
            query_vector=asset.vectors["clip"],
            limit=self.top_k * 3, # Get a larger set to re-rank
            owner_id=asset.owner_id
        )
        
        # Filter out self
        candidate_ids = [c["asset_id"] for c in candidates if c["asset_id"] != str(asset.id)]
        if not candidate_ids:
            return

        # 3. Re-rank based on multi-vector fusion
        # We fetch the actual Asset documents for the candidates to get their other vectors
        # (In a large-scale system, we'd store all vectors in Qdrant and do fusion there)
        related_assets = await Asset.find(Asset.id.in_([PydanticObjectId(aid) for aid in candidate_ids])).to_list()
        
        fused_scores: Dict[str, float] = {}
        
        for other in related_assets:
            # Weighted Cosine Similarity
            # 0.5 CLIP (Semantic)
            # 0.3 BLIP (Descriptive)
            # 0.2 MobileNet (Structural)
            
            s_clip = self._cosine_sim(asset.vectors["clip"], other.vectors.get("clip", []))
            s_blip = self._cosine_sim(asset.vectors["blip"], other.vectors.get("blip", []))
            s_mob  = self._cosine_sim(asset.vectors["mobilenet"], other.vectors.get("mobilenet", []))
            
            # Weighing logic
            total_score = (s_clip * 0.5) + (s_blip * 0.3) + (s_mob * 0.2)
            
            if total_score >= self.threshold:
                fused_scores[str(other.id)] = total_score

        # 4. Create Links
        for other_id, score in fused_scores.items():
            # Check if link already exists to avoid duplicates
            existing = await Link.find_one(
                Link.source_id == asset.id,
                Link.target_id == PydanticObjectId(other_id),
                Link.relation == "visually_similar_to"
            )
            if not existing:
                link = Link(
                    source_id=asset.id,
                    target_id=PydanticObjectId(other_id),
                    relation="visually_similar_to",
                    weight=score,
                    metadata={"method": "multi_vector_fusion"}
                )
                await link.save()
                logger.info(f"RelationProcessor: Linked {asset.id} -> {other_id} (score: {score:.4f})")

    def _cosine_sim(self, v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2:
            return 0.0
        a = np.array(v1)
        b = np.array(v2)
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))
