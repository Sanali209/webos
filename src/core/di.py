import abc
import functools
import inspect
import threading
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, get_type_hints

T = TypeVar("T")

class Lifetime(Enum):
    SINGLETON = auto()
    SCOPED = auto()
    TRANSIENT = auto()

class DIError(Exception):
    """Base exception for DI errors."""

class CircularDependencyError(DIError):
    """Raised when a circular dependency is detected."""

class ServiceNotFoundError(DIError):
    """Raised when a requested service is not registered."""

class Registration:
    def __init__(
        self,
        service_type: Type,
        implementation: Optional[Union[Type, Callable[..., Any]]] = None,
        lifetime: Lifetime = Lifetime.SINGLETON,
        instance: Any = None,
    ):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.instance = instance

class DIContainer:
    def __init__(self):
        self._registrations: Dict[Type, Registration] = {}
        self._lock = threading.RLock()
        self._scoped_instances: Dict[int, Dict[Type, Any]] = {}  # thread_id -> {type -> instance}
        self._resolution_stack: List[Type] = []

    def register(
        self,
        service_type: Type,
        implementation: Optional[Union[Type, Callable[..., Any]]] = None,
        instance: Optional[Any] = None,
        lifetime: Lifetime = Lifetime.SINGLETON,
    ):
        if implementation is None and instance is None:
            implementation = service_type

        with self._lock:
            self._registrations[service_type] = Registration(
                service_type, implementation, lifetime, instance
            )

    def resolve(self, service_type: Type[T]) -> T:
        from loguru import logger
        logger.debug(f"DI Resolving: {service_type}")
        with self._lock:
            if service_type not in self._registrations:
                # Try to auto-register ONLY if it's a concrete class and NOT a primitive
                if inspect.isclass(service_type) and not self._is_primitive(service_type) and not inspect.isabstract(service_type):
                    self.register(service_type)
                else:
                    raise ServiceNotFoundError(f"Service {service_type} not registered.")

            registration = self._registrations[service_type]

            if registration.lifetime == Lifetime.SINGLETON:
                if registration.instance is None:
                    registration.instance = self._create_instance(registration)
                return registration.instance

            if registration.lifetime == Lifetime.SCOPED:
                thread_id = threading.get_ident()
                if thread_id not in self._scoped_instances:
                    self._scoped_instances[thread_id] = {}
                
                instances = self._scoped_instances[thread_id]
                if service_type not in instances:
                    instances[service_type] = self._create_instance(registration)
                return instances[service_type]

            return self._create_instance(registration)

    def _create_instance(self, registration: Registration) -> Any:
        if registration.service_type in self._resolution_stack:
            cycle = " -> ".join([str(t) for t in self._resolution_stack + [registration.service_type]])
            raise CircularDependencyError(f"Circular dependency detected: {cycle}")

        self._resolution_stack.append(registration.service_type)
        try:
            if inspect.isclass(registration.implementation):
                return self._inject_constructor(registration.implementation)
            elif callable(registration.implementation):
                return registration.implementation()
            else:
                return registration.implementation
        finally:
            self._resolution_stack.pop()

    def _inject_constructor(self, cls: Type) -> Any:
        if cls.__init__ is object.__init__:
            return cls()

        signature = inspect.signature(cls.__init__)
        try:
            type_hints = get_type_hints(cls.__init__)
        except Exception:
            type_hints = {}
        
        args = {}
        for name, param in signature.parameters.items():
            if name == 'self':
                continue
            
            if name in type_hints:
                args[name] = self.resolve(type_hints[name])
            elif param.default is not inspect.Parameter.empty:
                continue
            elif param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            else:
                raise DIError(f"Cannot resolve parameter '{name}' of {cls}. No type hint or default value.")
        
        return cls(**args)

    def _is_primitive(self, cls: Type) -> bool:
        return cls in (str, int, float, bool, list, dict, set, tuple, bytes, Any)

    def inject(self, func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            signature = inspect.signature(func)
            try:
                type_hints = get_type_hints(func)
            except Exception:
                type_hints = {}
            
            new_kwargs = kwargs.copy()
            for name, param in signature.parameters.items():
                if name == 'self' or name in new_kwargs:
                    continue
                
                # Only inject if we have a type hint AND it's not a primitive OR it's explicitly registered
                if name in type_hints:
                    service_type = type_hints[name]
                    if service_type in self._registrations or (inspect.isclass(service_type) and not self._is_primitive(service_type)):
                        try:
                            new_kwargs[name] = self.resolve(service_type)
                        except ServiceNotFoundError:
                            if param.default is inspect.Parameter.empty:
                                raise
            
            return func(*args, **new_kwargs)
        return wrapper

# Global container instance
container = DIContainer()
container.register(DIContainer, instance=container)

def inject(func: Callable[..., T]) -> Callable[..., T]:
    return container.inject(func)
