# Architecture Overview

WebOS is designed as a **Modular Monolith**. It provides a robust, opinionated "Kernel" (Core) that handles essential system services, while allowing business logic and UI components to be encapsulated in independent "Modules". 

It is built on a stack of **FastAPI**, **NiceGUI**, and **Pluggy**.

## Core Principles

1. **Separation of Concerns**: The Kernel manages infrastructure (Auth, DB initialization, Module Loading, Service Registry) while Modules manage business domains.
2. **Convention over Configuration & Auto-Discovery**: Modules are auto-discovered from the `src/modules/` directory. If a module has a `models.py` or `router.py`, the system will automatically mount of them without explicit wiring, reducing boilerplate.
3. **Decoupled Extension**: Functionality that cannot be auto-discovered uses **Pluggy** hooks.

## The WebOS Spine (Kernel)

### 1. The Module Loader (`src.core.module_loader`)

The `ModuleLoader` singleton is responsible for discovering plugins, creating auto-discovery instances (e.g., auto-discovering API routes from `router.py`), and triggering lifecycle hooks across all loaded modules.

Modules can hook into various lifecycle events such as `on_startup`, `register_routes`, `register_ui`, and `register_tasks` defined in the `WebOSHookSpec` (`src.core.hooks`).

### 2. The Service Registry (`src.core.registry`)

The `ServiceRegistry` singleton manages dependency injection for the entire application. Instead of modules directly importing concrete implementations from one another (which creates circular dependencies), they depend on interfaces.

```python
from src.core.registry import registry
from src.modules.email.interfaces import EmailServiceInterface

# App startup: register a service
registry.register(EmailServiceInterface, SmtpEmailService())

# In a different module: Retrieve the service
mailer = registry.get(EmailServiceInterface)
mailer.send("hello@example.com")
```

### 3. FastAPI and NiceGUI

WebOS uses **FastAPI** as the foundational async web framework serving REST APIs, handling authentication, and orchestrating the backend.

**NiceGUI** runs on top of FastAPI to provide a reactive, server-driven UI. Modules can plug visual components directly into the main UI layout via UI slots, allowing seamless visual integration without needing to build separate front-end bundles.

---

**Full SDK reference**: See [Core API Reference](../reference/core_api.md) for complete specification of hooks and the ModuleLoader.
