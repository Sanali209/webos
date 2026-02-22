import io
import numpy as np
from typing import List, Optional, Any
from loguru import logger
from PIL import Image

from src.modules.dam.models import Asset, DetectedObject
from src.core.storage import storage_manager

class DetectionProcessor:
    """
    Object detection and localization using YOLOv8.
    """
    
    _model: Optional[Any] = None
    
    def __init__(self, confidence: float = 0.25):
        self.confidence = confidence
        self.applies_to = ["image"]

    @property
    def name(self) -> str:
        return "yolo_detector"

    @classmethod
    def get_model(cls):
        if cls._model is None:
            from ultralytics import YOLO
            logger.info("DetectionProcessor: Loading YOLOv8n model...")
            # Using the nano model for a good balance of speed and accuracy
            cls._model = YOLO('yolov8n.pt') 
        return cls._model

    async def process(self, asset: Asset) -> None:
        """
        Runs YOLO inference and populates asset.detected_objects.
        """
        try:
            file_bytes = await storage_manager.read_file(asset.storage_urn)
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        except Exception as e:
            logger.error(f"DetectionProcessor: Failed to load image {asset.id}: {e}")
            raise

        model = self.get_model()
        
        # Run inference
        results = model.predict(image, conf=self.confidence, verbose=False)
        
        detected = []
        img_w, img_h = image.size
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get normalized coordinates
                # YOLO boxes are [x1, y1, x2, y2] in pixels by default
                coords = box.xyxy[0].tolist() 
                x1, y1, x2, y2 = coords
                
                # Convert to normalized 0-1 range
                nx = x1 / img_w
                ny = y1 / img_h
                nw = (x2 - x1) / img_w
                nh = (y2 - y1) / img_h
                
                # Class info
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                conf = float(box.conf[0])
                
                detected.append(DetectedObject(
                    class_name=label,
                    confidence=conf,
                    bbox_x=nx,
                    bbox_y=ny,
                    bbox_w=nw,
                    bbox_h=nh,
                    model_name="yolov8n"
                ))

        asset.detected_objects = detected
        
        # Optionally extract features for relation analysis 
        # (YOLOv8 doesn't expose a simple 'embedding' per box as easily as CLIP, 
        # so we'll rely on the overall class composition for structural similarity 
        # in the RelationProcessor)
        
        logger.debug(f"DetectionProcessor: Found {len(detected)} objects in {asset.id}")
