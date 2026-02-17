import abc
from typing import Generic, List, Optional, TypeVar, Any
from .filters import FilterCriteria

T = TypeVar("T")

class IReadRepository(abc.ABC, Generic[T]):
    """Generic interface for read-only data access."""
    
    @abc.abstractmethod
    async def get(self, id: Any) -> Optional[T]:
        """Fetch a single entity by its unique identifier."""
        pass

    @abc.abstractmethod
    async def find(self, criteria: Optional[FilterCriteria] = None) -> List[T]:
        """Fetch multiple entities matching the given criteria."""
        pass

    @abc.abstractmethod
    async def count(self, criteria: Optional[FilterCriteria] = None) -> int:
        """Count entities matching the given criteria."""
        pass

class IWriteRepository(abc.ABC, Generic[T]):
    """Generic interface for write-heavy data access."""

    @abc.abstractmethod
    async def add(self, entity: T) -> T:
        """Persist a new entity."""
        pass

    @abc.abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass

    @abc.abstractmethod
    async def delete(self, id: Any) -> bool:
        """Remove an entity by its identifier."""
        pass

class IRepository(IReadRepository[T], IWriteRepository[T], Generic[T]):
    """Combined interface for full CRUD operations."""
    pass
