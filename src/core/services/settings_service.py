from typing import Any, Dict, Optional, Type
from pydantic import BaseModel
from loguru import logger
import src.core.db_models.module_settings as settings_models

class SettingsService:
    """
    Service to manage persistent module settings.
    """
    def __init__(self):
        # module_name -> Pydantic Model Class
        self._schemas: Dict[str, Type[BaseModel]] = {}
        # module_name -> instantiated Pydantic Model (live settings)
        self._cache: Dict[str, BaseModel] = {}

    def register_schema(self, module_name: str, schema_class: Type[BaseModel]):
        """Register a settings schema for a module."""
        self._schemas[module_name] = schema_class
        logger.debug(f"SettingsService: Registered schema for {module_name}")

    async def load_all(self):
        """Load all registered settings from DB on startup."""
        logger.info("SettingsService: Loading persistent settings...")
        for module_name, schema_class in self._schemas.items():
            try:
                doc = await settings_models.ModuleSettingsDoc.find_one(settings_models.ModuleSettingsDoc.module_name == module_name)
                if doc:
                    self._cache[module_name] = schema_class(**doc.values)
                else:
                    # Initialize with defaults if not in DB
                    self._cache[module_name] = schema_class()
            except Exception as e:
                logger.error(f"SettingsService: Error loading settings for {module_name}: {e}")
                # Fallback to defaults
                self._cache[module_name] = schema_class()

    def get(self, module_name: str) -> Optional[BaseModel]:
        """Get the current settings for a module."""
        return self._cache.get(module_name)

    def get_typed(self, module_name: str, schema_class: Type['T']) -> 'T':
        """Get the current settings, asserting a specific Pydantic schema type."""
        settings = self._cache.get(module_name)
        if settings is None:
            raise KeyError(f"No settings found for module '{module_name}'.")
        if not isinstance(settings, schema_class):
            raise TypeError(f"Settings for '{module_name}' is not of type {schema_class.__name__}.")
        return settings

    async def update(self, module_name: str, values: Dict[str, Any]):
        """Update settings for a module and persist to DB."""
        if module_name not in self._schemas:
            raise ValueError(f"Module {module_name} has no registered settings schema.")
        
        # Validate with Pydantic
        schema_class = self._schemas[module_name]
        updated_settings = schema_class(**values)
        
        # Persist
        doc = await settings_models.ModuleSettingsDoc.find_one(settings_models.ModuleSettingsDoc.module_name == module_name)
        if not doc:
            doc = settings_models.ModuleSettingsDoc(module_name=module_name, values=values)
            await doc.insert()
        else:
            doc.values = values
            await doc.save()
            
        # Update cache
        self._cache[module_name] = updated_settings
        logger.info(f"SettingsService: Updated settings for {module_name}")
        
        # TODO: Emit event on Event Bus for real-time reactivity
        from src.core.event_bus import event_bus as bus
        await bus.emit("settings:updated", {"module": module_name, "values": values})

# Singleton instance
settings_service = SettingsService()
