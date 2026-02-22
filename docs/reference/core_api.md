# Core API Reference

The Core provides the foundational APIs that WebOS modules rely on.

## Module Loader Hook Specifications

The `WebOSHookSpec` defines the extensibility points for the framework. Pluggy is used to implement these.

```python
from pluggy import HookimplMarker
hookimpl = HookimplMarker("webos")

@hookimpl
def register_models():
    """Returns a list of Beanie Document models to register."""
    from src.modules.inventory.models import Product
    return [Product]
```

**Key Hooks:**
- `register_routes(app: FastAPI)`
- `register_ui()`
- `on_startup()`
- `on_shutdown()`
- `register_settings()`

## Service Registry

The `ServiceRegistry` is the singleton dependency injection container.

```python
from src.core.registry import registry
from typing import Protocol

class EmailService(Protocol):
    def send(self, to: str, msg: str): ...
    
class MySmtpService:
    def send(self, to: str, msg: str):
        print("Sending...")

# Startup
registry.register(EmailService, MySmtpService())

# Usage
service = registry.get(EmailService)
service.send("test@example.com", "Hello!")
```

## Event Bus

The `EventBus` facilitates loosely coupled, asynchronous cross-module communication.

```python
import asyncio
from src.core.event_bus import event_bus

@event_bus.subscribe("order:created")
async def handle_order(envelope):
    print(f"Order created with ID: {envelope.payload['id']}")

async def main():
    # Fire an event
    await event_bus.emit("order:created", {"id": 1234})
```

## Storage / Abstract File System (AFS)

The AFS is used to address files regardless of their backend.

```python
from src.core.storage import afs

async def read_file():
    # URN format: fs://<datasource>/<path>
    content = await afs.read_text("fs://local/documents/plan.txt")
```
