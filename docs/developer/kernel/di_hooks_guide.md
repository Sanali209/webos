# Core Kernel Developer Guide: DI & Hooks

Welcome to the Web OS Engine core developer guide. This document explains how to interact with the Dependency Injection (DI) system and the Plugin Hook architecture.

## 1. Dependency Injection (DI)
The engine uses a thread-safe DI container located in `src.core.di`. It supports constructor injection and lifetime management.

### Registering Services
```python
from src.core.di import container, Lifetime

class MyService:
    pass

# Register as singleton (default)
container.register(MyService)

# Register with explicit lifetime
container.register(MyService, lifetime=Lifetime.TRANSIENT)
```

### Injecting Dependencies
You can use constructor injection or the `@inject` decorator.

**Constructor Injection (Preferred):**
```python
class Consumer:
    def __init__(self, service: MyService):
        self.service = service
```

**Function Injection:**
```python
from src.core.di import inject

@inject
def handle_action(service: MyService):
    pass
```

## 2. Plugin Hooks (pluggy)
The engine uses `pluggy` to allow modules to extend core functionality.

### Available Hooks
- `post_setup()`: Async. Called after all modules are loaded.
- `on_module_load(module)`: Async. Called when a specific module is loaded.
- `mount_ui()`: Synchronous. Used to register UI routes.

### Implementing a Hook
In your module class:
```python
from src.core.hooks import hookimpl

class MyModule(BaseModule):
    @hookimpl
    async def post_setup(self):
        print("Kernel is ready!")
```

## 3. Exception Handling
Always inherit from `src.core.exceptions.BaseEngineException` for engine-related errors. This ensures they are caught and logged correctly by the kernel's error boundaries.
