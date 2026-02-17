import abc
from typing import Protocol, runtime_checkable

class IModule(abc.ABC):
    """Abstract Base Class defining the interface for all engine modules."""
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def version(self) -> str:
        pass

    @abc.abstractmethod
    async def initialize(self) -> None:
        """Called during engine boot to initialize the module."""
        pass

    @abc.abstractmethod
    async def shutdown(self) -> None:
        """Called during engine shutdown to clean up resources."""
        pass

from loguru import logger
from .di import DIContainer, container

class BaseModule(IModule):
    """Base class providing a default implementation of IModule."""
    name: str = "base_module"
    version: str = "0.1.0"

    def __init__(self, di_container: DIContainer = container):
        self._di = di_container
        self.logger = logger.bind(module=self.name)

    async def initialize(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass
