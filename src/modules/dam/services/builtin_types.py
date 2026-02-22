from typing import List
from src.modules.dam.schemas.asset_type import AssetTypeDefinition

class ImageAssetType(AssetTypeDefinition):
    @property
    def type_id(self) -> str:
        return "image"
        
    @property
    def accepted_mimes(self) -> List[str]:
        return ["image/"]

class VideoAssetType(AssetTypeDefinition):
    @property
    def type_id(self) -> str:
        return "video"
        
    @property
    def accepted_mimes(self) -> List[str]:
        return ["video/"]

class AudioAssetType(AssetTypeDefinition):
    @property
    def type_id(self) -> str:
        return "audio"
        
    @property
    def accepted_mimes(self) -> List[str]:
        return ["audio/"]

class DocumentAssetType(AssetTypeDefinition):
    @property
    def type_id(self) -> str:
        return "document"
        
    @property
    def accepted_mimes(self) -> List[str]:
        return [
            "application/pdf", 
            "text/", 
            "application/msword", 
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        ]

class UrlAssetType(AssetTypeDefinition):
    @property
    def type_id(self) -> str:
        return "url"
        
    @property
    def accepted_mimes(self) -> List[str]:
        return ["text/uri-list"]
        
    def describe(self) -> str:
        return "Web Bookmark"
