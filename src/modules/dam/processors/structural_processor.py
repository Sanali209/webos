from typing import List, Optional, Any
from src.modules.dam.models import Asset
from src.core.storage import storage_manager

class StructuralProcessor:
    """
    Extracts structural/geometric features using MobileNet.
    Uses 'transformers' to avoid 'torchvision' extension issues in some environments.
    """
    
    _model: Optional[Any] = None
    _processor: Optional[Any] = None
    
    def __init__(self):
        self.applies_to = ["image"]

    @property
    def name(self) -> str:
        return "structural_features"

    @classmethod
    def get_resources(cls):
        if cls._model is None:
            import torch
            from loguru import logger
            from transformers import AutoImageProcessor, AutoModel
            
            logger.info("StructuralProcessor: Loading MobileNet feature extractor...")
            # We use a lightweight MobileNetV2 from HuggingFace
            model_name = "google/mobilenet_v2_1.0_224"
            cls._processor = AutoImageProcessor.from_pretrained(model_name)
            cls._model = AutoModel.from_pretrained(model_name)
            cls._model.eval()
            
            if torch.cuda.is_available():
                cls._model.to("cuda")
        return cls._model, cls._processor

    async def process(self, asset: Asset) -> None:
        """
        Generates a 1280-dimensional structural feature vector.
        """
        import io
        import torch
        from PIL import Image
        from loguru import logger
        
        try:
            file_bytes = await storage_manager.read_file(asset.storage_urn)
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        except Exception as e:
            logger.error(f"StructuralProcessor: Failed to load image {asset.id}: {e}")
            raise

        model, processor = self.get_resources()
        device = next(model.parameters()).device
        
        # Preprocess
        inputs = processor(images=image, return_tensors="pt").to(device)
        
        # Inference
        with torch.no_grad():
            outputs = model(**inputs)
            # Use pooler_output or mean pool the last hidden state
            # MobileNetV2 in transformers usually has pooler_output (1280)
            if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
                vector = outputs.pooler_output[0].tolist()
            else:
                # Fallback to mean pooling
                vector = outputs.last_hidden_state.mean(dim=1)[0].tolist()

        # Store in asset
        asset.vectors["mobilenet"] = vector
        logger.debug(f"StructuralProcessor: Extracted {len(vector)} features for {asset.id}")
