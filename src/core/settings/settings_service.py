from typing import Any, List, Optional
import diskcache
from loguru import logger
from pydantic import BaseModel
from src.core.service import BaseService
from src.core.filters import FilterCriteria, Operator
from src.core.infrastructure.persistence.beanie_adapter import BeanieRepository
from src.core.infrastructure.persistence.models import SettingDocument

class SettingEntity(BaseModel):
    key: str
    value: Any
    scope: str = "global"

class SettingsRepository(BeanieRepository[SettingEntity, SettingDocument]):
    def _to_entity(self, doc: SettingDocument) -> SettingEntity:
        return SettingEntity(key=doc.key, value=doc.value, scope=doc.scope)

    def _to_document(self, entity: SettingEntity) -> SettingDocument:
        return SettingDocument(key=entity.key, value=entity.value, scope=entity.scope)

class SettingsService(BaseService[SettingEntity]):
    """Centralized service for managing engine and module settings."""
    
    def __init__(self, repository: SettingsRepository, cache_dir: str = ".cache/settings"):
        super().__init__()
        self.repo = repository
        self.cache = diskcache.Cache(cache_dir)
        self.logger.info(f"Settings cache initialized at {cache_dir}")

    async def get_setting(self, key: str, scope: str = "global") -> Any:
        """Fetch a setting, checking the cache first."""
        cache_key = f"{scope}:{key}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        criteria = FilterCriteria().where("key", Operator.EQ, key).where("scope", Operator.EQ, scope)
        settings = await self.repo.find(criteria)
        
        if settings:
            value = settings[0].value
            self.cache[cache_key] = value
            return value
        
        return None

    async def set_setting(self, key: str, value: Any, scope: str = "global"):
        """Update a setting and invalidate its cache."""
        criteria = FilterCriteria().where("key", Operator.EQ, key).where("scope", Operator.EQ, scope)
        existing = await self.repo.find(criteria)
        
        if existing:
            entity = existing[0]
            entity.value = value
            await self.execute_safely("Update Setting", self.repo.update, entity)
        else:
            entity = SettingEntity(key=key, value=value, scope=scope)
            await self.execute_safely("Create Setting", self.repo.add, entity)
        
        cache_key = f"{scope}:{key}"
        self.cache[cache_key] = value
        self.logger.info(f"Setting updated: {cache_key}")

    def invalidate_cache(self, key: Optional[str] = None, scope: str = "global"):
        """Invalidate cache entries."""
        if key:
            cache_key = f"{scope}:{key}"
            if cache_key in self.cache:
                del self.cache[cache_key]
        else:
            self.cache.clear()
