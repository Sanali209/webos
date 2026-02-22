import subprocess
import json
import shutil
from typing import Dict, Any
from pathlib import Path
from loguru import logger
from src.modules.dam.models import Asset
from src.modules.dam.drivers.base import BaseAssetDriver

class VideoDriver(BaseAssetDriver):
    """
    Extracts metadata from video files using `ffprobe`.
    Requires `ffprobe` executable within the system PATH.
    """

    def __init__(self):
        self.has_ffprobe = shutil.which("ffprobe") is not None
        if not self.has_ffprobe:
            logger.warning("VideoDriver: 'ffprobe' not found in system PATH. Video metadata extraction is disabled.")

    @property
    def type_id(self) -> str:
        return "video"
        
    def extract_metadata(self, asset: Asset, file_path: Path) -> Dict[str, Any]:
        """Runs within an asyncio.to_thread context."""
        if not self.has_ffprobe:
            return {"error": "ffprobe not installed"}
        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]
        
        try:
            # Capture output ensuring termination natively against hung probes 
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning(f"VideoDriver ffprobe failed for {file_path.name}: {result.stderr}")
                return {"error": "ffprobe decoding error"}
                
            data = json.loads(result.stdout)
            
            metadata = {
                "duration_s": float(data.get("format", {}).get("duration", 0.0)),
                "bitrate": int(data.get("format", {}).get("bit_rate", 0)),
                "has_audio": False,
            }

            # Map streams scanning for structural components natively
            for stream in data.get("streams", []):
                codec_type = stream.get("codec_type")
                
                if codec_type == "video" and "width" not in metadata:
                    metadata["width"] = int(stream.get("width", 0))
                    metadata["height"] = int(stream.get("height", 0))
                    metadata["codec"] = stream.get("codec_name")
                    
                    # Convert framerate "30/1" back down manually 
                    fps_str = stream.get("r_frame_rate", "0/1")
                    if "/" in fps_str:
                        num, den = fps_str.split("/")
                        if int(den) > 0:
                            metadata["fps"] = round(float(num) / float(den), 2)
                            
                elif codec_type == "audio":
                    metadata["has_audio"] = True
                    metadata["audio_codec"] = stream.get("codec_name")

            return {k: v for k, v in metadata.items() if v}
            
        except FileNotFoundError:
            logger.error("VideoDriver requires external 'ffprobe' installed to the system PATH.")
            return {"error": "ffprobe not found"}
            
        except subprocess.TimeoutExpired:
            logger.warning(f"VideoDriver timed out inspecting {file_path.name}.")
            return {"error": "timeout"}
            
        except Exception as e:
            logger.error(f"VideoDriver encountered critical error processing {file_path.name}: {e}")
            return {"error": "corrupt video format"}
