# Module System

The WebOS Module System is built on the principle of **Convention over Configuration**. By following a simple folder structure, your module is automatically discovered, registered, and integrated into the Kernel.

## Standard Directory Structure

A typical WebOS module follows this layout:

```text
src/modules/your_module/
├── __init__.py      # Required for discovery
├── models.py        # Beanie (MongoDB) models
├── router.py        # FastAPI API endpoints
├── ui.py            # NiceGUI pages and components
├── hooks.py         # Pluggy-based system hooks (startup/shutdown)
└── data/            # Module-specific static data
```

## How Auto-Discovery Works

The `ModuleLoader` (in `src.core.module_loader`) scans the `src/modules/` directory at startup and performs the following actions:

### 1. Model Registration
If `models.py` exists, the loader imports it and registers all Beanie `Document` classes with the database engine.

### 2. Router Wiring
If `router.py` exists, the loader imports it and attaches the `router` instance to the main FastAPI app under the `/api` prefix.

### 3. UI Integration
If `ui.py` exists, the loader imports it. This allows the module to define `@ui.page` routes and register itself with the `ui_registry`.

### 4. Hook Execution
If `hooks.py` exists, it is registered with the `pluggy` HookRelay. This allows the module to respond to system-wide events like `on_startup` and `on_shutdown`.

## Creating a Module

To create a new module, simply create a folder in `src/modules/` with an `__init__.py`. The Kernel will immediately recognize it as part of the ecosystem.

### Best Practices
- **Isolation**: Minimize imports between modules. Use the [Event Bus](../tutorials/core_concepts.md) for communication.
- **Naming**: Use lowercase, snake_case for folder names.
- **Metadata**: Register your app in `ui.py` so it appears on the [Launchpad](./layout_system.md).

---

## Next Steps
- Learn how to [Create Your First Module](../tutorials/create_module.md).
- Understand the [UI & Layout System](./layout_system.md).
