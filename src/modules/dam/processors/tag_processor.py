import io
import numpy as np
import pandas as pd
from typing import List, Optional, Any, Dict
from loguru import logger
from PIL import Image

from src.modules.dam.models import Asset
from src.core.storage import storage_manager

class TagProcessor:
    """
    Automated tagging using SmileWolf WD14 Tagger (ONNX).
    """
    
    _session: Optional[Any] = None
    _tags: Optional[List[str]] = None
    
    def __init__(self, threshold: float = 0.35):
        self.threshold = threshold
        self.applies_to = ["image"]
        self.model_repo = "SmilingWolf/wd-v1-4-convnext-tagger-v2"

    @property
    def name(self) -> str:
        return "tagger"

    @classmethod
    def load_model(cls):
        """
        Loads ONNX session and tag CSV.
        """
        if cls._session is None:
            import onnxruntime as ort
            from huggingface_hub import hf_hub_download
            
            logger.info("TagProcessor: Downloading/Loading WD14 ONNX model...")
            
            model_path = hf_hub_download(repo_id="SmilingWolf/wd-v1-4-convnext-tagger-v2", filename="model.onnx")
            tags_path = hf_hub_download(repo_id="SmilingWolf/wd-v1-4-convnext-tagger-v2", filename="selected_tags.csv")
            
            cls._session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
            
            # Load tags CSV
            df = pd.read_csv(tags_path)
            # The CSV usually has 'name' as the tag
            cls._tags = df['name'].tolist()
            
        return cls._session, cls._tags

    async def process(self, asset: Asset) -> None:
        """
        Runs inference and populates asset.ai_tags.
        """
        try:
            file_bytes = await storage_manager.read_file(asset.storage_urn)
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        except Exception as e:
            logger.error(f"TagProcessor: Failed to load image {asset.id}: {e}")
            raise

        session, tag_names = self.load_model()
        
        # Preprocessing (WD14 likes 448x448)
        image = image.resize((448, 448), resample=Image.Resampling.LANCZOS)
        img_arr = np.array(image).astype(np.float32)
        # RGB to BGR as preferred by some WD14 versions, but usually RGB is fine for these.
        # However, the standard implementation often uses BGR.
        img_arr = img_arr[:, :, ::-1] 
        img_arr = np.expand_dims(img_arr, axis=0) # [1, 448, 448, 3]

        # Inference
        input_name = session.get_inputs()[0].name
        label_name = session.get_outputs()[0].name
        probs = session.run([label_name], {input_name: img_arr})[0][0]

        # Filter by threshold
        found_tags = []
        confidences = {}
        
        for i, p in enumerate(probs):
            if p >= self.threshold:
                tag = tag_names[i]
                # Filter out meta tags like 'rating:safe' if desired, or keep all
                found_tags.append(tag)
                confidences[tag] = float(p)

        # Update Asset
        asset.ai_tags = list(set(asset.ai_tags + found_tags))
        if "ai_confidences" not in asset.metadata:
            asset.metadata["ai_confidences"] = {}
        asset.metadata["ai_confidences"].update(confidences)
        
        logger.debug(f"TagProcessor: Generated {len(found_tags)} tags for {asset.id}")
