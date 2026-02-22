from typing import List, Optional, Any
from loguru import logger
import io

from src.modules.dam.models import Asset
from src.core.storage import storage_manager

class BLIPProcessor:
    """
    Generates human-readable captions using BLIP.
    """
    
    _processor: Optional[Any] = None
    _model: Optional[Any] = None
    
    def __init__(self):
        self.applies_to = ["image"]

    @property
    def name(self) -> str:
        return "blip"

    @classmethod
    def load_models(cls):
        if cls._model is None:
            import torch
            from transformers import BlipProcessor, BlipForConditionalGeneration
            logger.info("BLIPProcessor: Loading 'blip-image-captioning-base' model...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            cls._processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            cls._model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)
        return cls._processor, cls._model

    async def process(self, asset: Asset) -> None:
        """
        Generates a caption and updates asset.ai_caption.
        """
        from PIL import Image
        try:
            file_bytes = await storage_manager.read_file(asset.storage_urn)
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        except Exception as e:
            logger.error(f"BLIPProcessor: Failed to load image {asset.storage_urn}: {e}")
            raise

        processor, model = self.load_models()
        device = model.device

        # Prepare inputs
        inputs = processor(image, return_tensors="pt").to(device)

        # 1. Generate caption
        out = model.generate(**inputs, max_new_tokens=50)
        caption = processor.decode(out[0], skip_special_tokens=True)

        # 2. Extract Embedding (using the vision model's pooled output)
        with torch.no_grad():
            vision_outputs = model.vision_model(
                pixel_values=inputs.pixel_values,
                return_dict=True
            )
            # Use the pooler_output (usually the first token or mean pooled)
            embedding = vision_outputs.pooler_output[0].tolist()

        # Update asset
        asset.ai_caption = caption
        asset.vectors["blip"] = embedding
        logger.debug(f"BLIPProcessor: Generated caption and {len(embedding)}-d embedding for {asset.id}")
