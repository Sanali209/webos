from typing import Dict, Any
from pathlib import Path
from PIL import Image, ImageOps
from loguru import logger
from src.modules.dam.models import Asset
from src.modules.dam.drivers.base import BaseAssetDriver

class ImageDriver(BaseAssetDriver):
    """
    Extracts metadata from image files using Pillow.
    Handles dimensions, color space, and basic EXIF including GPS float mapping.
    """
    
    @property
    def type_id(self) -> str:
        return "image"
        
    def extract_metadata(self, asset: Asset, file_path: Path) -> Dict[str, Any]:
        """Runs within asyncio.to_thread context block off-loop."""
        try:
            with Image.open(str(file_path)) as img:
                # Normalise orientation reading dimensions
                img = ImageOps.exif_transpose(img)
                
                metadata = {
                    "width": img.width,
                    "height": img.height,
                    "color_space": img.mode,
                }
                
                # Fetch Bit Depth where natively populated
                if hasattr(img, "bits"):
                    metadata["bit_depth"] = img.bits
                
                # Retrieve standard EXIF natively
                exif = img.getexif()
                if exif:
                    # Resolve to standardized IFD identifiers using Pillow native values 
                    # 271: Make, 272: Model, 306: DateTime
                    metadata["make"] = exif.get(271)
                    metadata["model"] = exif.get(272)
                    metadata["taken_at"] = exif.get(306)
                    
                    # GPS resolution resolving IFD 34853 (GPSInfo)
                    gps_info = exif.get_ifd(34853)
                    if gps_info:
                        def _to_decimal(dms, ref):
                            if not dms or not ref: return None
                            d = float(dms[0]) + float(dms[1])/60 + float(dms[2])/3600
                            return -d if ref in ['S', 'W'] else d
                            
                        # 1: GPSLatitudeRef, 2: GPSLatitude, 3: GPSLongitudeRef, 4: GPSLongitude
                        lat = _to_decimal(gps_info.get(2), gps_info.get(1))
                        lon = _to_decimal(gps_info.get(4), gps_info.get(3))
                        
                        if lat and lon:
                            metadata["gps_lat"] = round(lat, 6)
                            metadata["gps_lon"] = round(lon, 6)
                
                # Clean null keys returning a standardized JSON safe dictionary
                return {k: v for k, v in metadata.items() if v is not None}
                
        except Exception as e:
            logger.warning(f"ImageDriver failed to process {file_path.name}: {e}")
            return {"error": "corrupt image"}
