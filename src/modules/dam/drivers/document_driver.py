import fitz
import docx
from typing import Dict, Any
from pathlib import Path
from loguru import logger
from src.modules.dam.models import Asset
from src.modules.dam.drivers.base import BaseAssetDriver

class DocumentDriver(BaseAssetDriver):
    """
    Extracts metadata from PDF and Word documents using `PyMuPDF` and `python-docx`.
    Evaluates structures terminating early against encrypted payloads safely.
    """

    @property
    def type_id(self) -> str:
        return "document"
        
    def extract_metadata(self, asset: Asset, file_path: Path) -> Dict[str, Any]:
        """Runs within an asyncio.to_thread context block."""
        ext = file_path.suffix.lower()
        try:
            if ext == ".pdf":
                return self._extract_pdf(file_path)
            elif ext in [".docx", ".doc"]:
                return self._extract_docx(file_path)
            elif ext in [".txt", ".md"]:
                return self._extract_text(file_path)
            return {}
            
        except fitz.fitz.FileDataError:
            return {"error": "corrupt document"}
            
        except Exception as e:
            logger.error(f"DocumentDriver failed processing {file_path.name}: {e}")
            return {"error": "extraction failed"}

    def _extract_pdf(self, path: Path) -> Dict[str, Any]:
        doc = fitz.open(str(path))
        try:
            if doc.is_encrypted:
                return {"error": "encrypted"}
                
            metadata = {
                "page_count": doc.page_count,
            }
            
            # Fetch native descriptors inside the file standard
            meta = doc.metadata
            if meta:
                title = meta.get("title")
                author = meta.get("author")
                if title: metadata["title"] = title
                if author: metadata["author"] = author
                
            # Attempt light word counting scanning elements
            words = 0
            for i in range(min(5, doc.page_count)):  # Estimate based on first 5 pages mapping
                text = doc[i].get_text("text")
                words += len(text.split())
            
            # Calculate average per-page projecting across file natively
            if words > 0:
                avg_words = words / min(5, doc.page_count)
                metadata["word_count_estimate"] = int(avg_words * doc.page_count)
                
            return metadata
        finally:
            doc.close()

    def _extract_docx(self, path: Path) -> Dict[str, Any]:
        doc = docx.Document(str(path))
        
        metadata = {}
        
        props = doc.core_properties
        if props.title: metadata["title"] = props.title
        if props.author: metadata["author"] = props.author
        
        # Word counting based on structural elements mapped cleanly
        words = sum(len(p.text.split()) for p in doc.paragraphs)
        if words > 0:
            metadata["word_count_estimate"] = words
            
        # Pages aren't reliably tracked by Word natively without rendering contexts
        return metadata

    def _extract_text(self, path: Path) -> Dict[str, Any]:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            metadata = {
                "word_count_estimate": len(text.split())
            }
            return metadata
        except IOError:
            return {"error": "read failed"}
