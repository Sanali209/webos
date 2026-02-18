from typing import Any, Dict
from beanie import Indexed
from src.core.models import CoreDocument

class ModuleSettingsDoc(CoreDocument):
    """
    Database document to store serialized settings for each module.
    """
    module_name: str = Indexed(unique=True)
    values: Dict[str, Any] = {}

    class Settings:
        name = "system_settings"
