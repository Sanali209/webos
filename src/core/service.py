import abc
from typing import Generic, TypeVar, Optional, Any
from loguru import logger
from .repository import IRepository
from .exceptions import BaseEngineException

T = TypeVar("T")

class BaseService(Generic[T], abc.ABC):
    """Base class for all domain services, providing logging and standard patterns."""
    
    def __init__(self):
        self.logger = logger.bind(service=self.__class__.__name__)

    async def execute_safely(self, operation_name: str, func, *args, **kwargs):
        """Standard wrapper for error handling and logging."""
        self.logger.info(f"Executing {operation_name}...")
        try:
            result = await func(*args, **kwargs)
            self.logger.success(f"{operation_name} completed successfully.")
            return result
        except Exception as e:
            self.logger.error(f"Error during {operation_name}: {str(e)}")
            if isinstance(e, BaseEngineException):
                raise
            raise BaseEngineException(f"Unexpected error in {self.__class__.__name__}", details={"original_error": str(e)})

class UnitOfWork(abc.ABC):
    """Context manager for atomicity across multiple repositories."""
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        else:
            await self.commit()

    @abc.abstractmethod
    async def commit(self):
        pass

    @abc.abstractmethod
    async def rollback(self):
        pass
