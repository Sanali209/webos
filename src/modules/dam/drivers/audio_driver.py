import mutagen
from typing import Dict, Any
from pathlib import Path
from loguru import logger
from src.modules.dam.models import Asset
from src.modules.dam.drivers.base import BaseAssetDriver

class AudioDriver(BaseAssetDriver):
    """
    Extracts metadata from audio files using `mutagen`.
    Supports ID3 mapping natively traversing stream attributes.
    """

    @property
    def type_id(self) -> str:
        return "audio"
        
    def extract_metadata(self, asset: Asset, file_path: Path) -> Dict[str, Any]:
        """Runs within an asyncio.to_thread context block."""
        try:
            audio = mutagen.File(str(file_path), easy=True)
            if audio is None:
                return {}
                
            metadata = {}
            
            # Fetch base technicals safely
            if hasattr(audio, "info") and audio.info:
                metadata["duration_s"] = float(getattr(audio.info, "length", 0.0))
                metadata["bitrate"] = int(getattr(audio.info, "bitrate", 0))
                metadata["sample_rate"] = int(getattr(audio.info, "sample_rate", 0))
                metadata["channels"] = int(getattr(audio.info, "channels", 0))

            # Fetch explicit ID3 tag classifications
            tags = ["title", "artist", "album", "tracknumber"]
            for tag in tags:
                value = audio.get(tag)
                if value and isinstance(value, list) and len(value) > 0:
                    # Clean trailing artifacts
                    cleaned = str(value[0]).split("\x00")[0]
                    if tag == "tracknumber":
                        # Track numbers are usually formatted as `1/12`.
                        cleaned = cleaned.split("/")[0]
                        metadata["track_number"] = int(cleaned) if cleaned.isdigit() else None
                    else:
                        metadata[tag] = cleaned

            return {k: v for k, v in metadata.items() if v}
            
        except mutagen.MutagenError as e:
            logger.warning(f"AudioDriver (mutagen) failed processing {file_path.name}: {e}")
            return {"error": "corrupt audio format"}
            
        except Exception as e:
            logger.error(f"AudioDriver (mutagen) encountered critical error processing {file_path.name}: {e}")
            return {"error": "extraction failed"}
