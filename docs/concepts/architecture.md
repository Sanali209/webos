# Architecture Overview

WebOS is designed as a **Modular Monolith**. It provides a robust, opinionated "Kernel" (Core) that handles essential system services, while allowing business logic to be encapsulated in independent "Modules".

## Core Principles

1. **Separation of Concerns**: The Kernel manages infrastructure (Auth, DB, Event Bus, Tasks) while Modules manage business domains.
2. **Convention over Configuration**: Modules are auto-discovered and auto-wired based on standard file names (e.g., `router.py`, `models.py`).
3. **Decoupled Communication**: Modules communicate primarily via the asynchronous Event Bus.

## The WebOS Spine (Kernel)

### 1. The Service Registry (DI)
The `ServiceRegistry` is a singleton that manages dependency injection. It allows modules to register implementations for generic interfaces.

```python
from src.core.registry import registry

# Register a service
registry.register("email_service", SMTPEmailService())

# Retrieve a service
mailer = registry.get("email_service")
```

### 2. The Event Bus
The Event Bus facilitates loosely coupled communication between modules. When something interesting happens in Module A, it emits an event; Module B can listen and react.

```python
from src.core.event_bus import bus

# Emit an event
await bus.emit("user:logged_in", {"user_id": "123"})

# Subscribe to an event
@bus.on("user:logged_in")
async def send_welcome_email(payload):
    print(f"Sending welcome to {payload['user_id']}")
```

### 3. Unified Storage (AFS)
The Abstract File System (AFS) provides a single API for interacting with different storage backends (Local, S3) using URNs.

- Local: `fs://local/uploads/resume.pdf`
- S3: `fs://s3/backups/db.tar.gz`

### 4. Background Tasks (TaskIQ)
Long-running operations are offloaded to workers using TaskIQ. Context (User, Trace ID) is automatically propagated to the worker.

---

## The Module Lifecycle

Modules are loaded during the application startup phase in `main.py`:

1. **Discovery**: Loader scans `src/modules/*`.
2. **Initialization**: Models are registered with Beanie; Routers are mounted to FastAPI.
3. **Hook Execution**: Modules can hook into `startup` and `shutdown` events via `pluggy`.

---

## Next Steps
- Dive deeper into the [Module System](./module_system.md).
- Understand the [Authentication & Security](./auth_system.md) layer.
- Learn about [UI & Layout System](./layout_system.md).
