from typing import Any, Dict, Type, TypeVar, Optional

T = TypeVar("T")


class ServiceRegistry:
    _instance: Optional["ServiceRegistry"] = None
    _services: Dict[Type[Any], Any] = {}

    def __new__(cls) -> "ServiceRegistry":
        if cls._instance is None:
            cls._instance = super(ServiceRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, interface: Type[T], implementation: Any) -> None:
        """
        Register an implementation for a given interface.
        """
        cls._services[interface] = implementation

    @classmethod
    def get(cls, interface: Type[T]) -> T:
        """
        Retrieve the implementation for a given interface.
        Raises ValueError if not registered.
        """
        service = cls._services.get(interface)
        if not service:
            raise ValueError(f"Service for {interface.__name__} not registered.")
        return service

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered services (useful for testing).
        """
        cls._services.clear()


registry = ServiceRegistry()
