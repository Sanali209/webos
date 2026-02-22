from typing import List, Optional, Any
from loguru import logger
import io

from src.modules.dam.models import Asset
from src.core.storage import storage_manager
from src.core.registry import ServiceRegistry

class CLIPProcessor:
    """
    Generates semantic embeddings using CLIP.
    """
    
    _model: Optional[Any] = None
    
    def __init__(self):
        self.type_id = "clip"
        self.applies_to = ["image"]

    @property
    def name(self) -> str:
        return "clip"

    @classmethod
    def get_model(cls) -> Any:
        if cls._model is None:
            import torch
            from sentence_transformers import SentenceTransformer
            logger.info("CLIPProcessor: Loading 'clip-ViT-B-32' model...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            cls._model = SentenceTransformer('clip-ViT-B-32', device=device)
        return cls._model

    async def process(self, asset: Asset) -> None:
        """
        Loads image from storage, encodes, and indexes in Qdrant.
        """
        from PIL import Image
        
        # 1. Load image bytes from AFS
        try:
            file_bytes = await storage_manager.read_file(asset.storage_urn)
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        except Exception as e:
            logger.error(f"CLIPProcessor: Failed to load image {asset.storage_urn}: {e}")
            raise

        # 2. Generate embedding
        model = self.get_model()
        embedding = model.encode(image).tolist()

        # 3. Index in Qdrant via VectorService
        from src.modules.dam.services.vector_service import VectorService
        vs = ServiceRegistry.get(VectorService)
        if vs.is_available:
            await vs.upsert_asset(asset, embedding)
        else:
            logger.warning("CLIPProcessor: VectorService unavailable, skipping Qdrant index.")
            # Store at least in MongoDB
            asset.vectors["clip"] = embedding
            await asset.save()

    def encode_text(self, text: str) -> List[float]:
        """
        Encodes query text for semantic search.
        """
        model = self.get_model()
        return model.encode(text).tolist()
