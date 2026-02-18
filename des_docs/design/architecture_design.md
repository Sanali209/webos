# Architecture Design Document

## 1. System Overview

The WebOS Framework is a **Modular Monolith** architecture. It combines the simplicity of a monolithic deployment with the extensibility of a plugin-based system.

### 1.1. System Context (C4 Level 1)

```mermaid
C4Context
    title System Context Diagram for WebOS Framework

    Person(user, "User", "Internal employee using the tools")
    System(webos, "WebOS Framework", "The modular platform hosting business applications")
    System_Ext(s3, "Object Storage", "MinIO / S3 for file storage")
    System_Ext(mongo, "MongoDB", "NoSQL Database for structured data")

    Rel(user, webos, "Uses", "HTTPS")
    Rel(webos, s3, "Stores/Retrieves files", "S3 API")
    Rel(webos, mongo, "Reads/Writes data", "TCP/IP")
```

## 2. Container Architecture (C4 Level 2)

The system runs as a single deployable unit (container/process) but is logically divided.

```mermaid
C4Container
    title Container Diagram

    Person(user, "User", "Web Browser")

    Container_Boundary(app_boundary, "WebOS Application") {
        Component(nicegui, "NiceGUI Frontend", "Python/Vue/Quasar", "Renders UI, manages state per client via WebSockets")
        Component(command_palette, "Command Palette", "NiceGUI HUD", "Global Ctrl+K navigation and CLI-in-browser")
        Component(fastapi, "FastAPI Backend", "Python", "Handles HTTP API requests, Auth, static files")
        Component(taskiq, "TaskIQ Worker", "Python", "Background task processing (in-process or separate)")
        Component(pluggy, "Plugin Manager", "Pluggy", "Loads and manages modules")
        
        Component(core, "Core Kernel", "Python Module", "Base services, Event Bus, Auth, Settings")
        Component(modules, "Business Modules", "Python Packages", "Inventory, HR, Analytics, etc.")
    }

    System_Ext(db, "MongoDB", "Data persistence")

    Rel(user, nicegui, "Interacts", "WebSocket / HTTP")
    Rel(nicegui, fastapi, "Runs on", "Starlette/Uvicorn")
    Rel(fastapi, core, "Uses")
    Rel(taskiq, core, "Uses")
    Rel(pluggy, modules, "Loads")
    Rel(modules, core, "Depends on")
    Rel(core, db, "Beanie ODM", "TCP")
```

## 3. Module Architecture

Each module follows a strict structure to ensure isolation and pluggability.

```mermaid
classDiagram
    class CoreKernel {
        +register_router(router)
        +register_event_listener(event, callback)
        +register_event_listener(event, callback)
        +register_ui_slot(slot_name, component)
        +register_admin_panel(panel_config)
        +get_service(service_name)
    }

    class MyModule {
        +setup(core: CoreKernel)
    }

    class ModuleRouter {
        +get_items()
        +create_item()
    }

    class ModuleService {
        +business_logic()
    }

    class ModuleDocument {
        +field1: str
        +field2: int
    }

    MyModule ..> CoreKernel : Uses
    MyModule --> ModuleRouter : Registers
    MyModule --> ModuleService : Instantiates
    ModuleService --> ModuleDocument : Uses (Beanie)

    class StorageModule {
        +mount_source(source: DataSource)
        +list(path)
        +open(path)
    }

    class DataSource {
        <<interface>>
        +connect()
        +list_files()
        +get_stream()
    }

    StorageModule --> DataSource : Manages
    class S3Source
    class LocalSource
    S3Source ..|> DataSource
    LocalSource ..|> DataSource
```

## 4. Key Flows

### 4.1. Request Flow (UI Interaction)
1.  **User Event**: User clicks "Save" on a form in NiceGUI.
2.  **WebSocket Message**: Event sent to server via NiceGUI connection.
3.  **Event Handler**: Python callback in the specific Module triggered.
4.  **Service Call**: Callback invokes `ModuleService.save_entity()`.
5.  **Access Control**: `@require_permission` decorator checks `self.current_user` permissions.
6.  **Database**: `ModuleDocument.save()` writes to MongoDB via Beanie.
7.  **Core Event**: Service emits `entity:saved` event via Core Event Bus.
8.  **Feedback**: `self.messenger.success()` sends toast back to User UI.

### 4.2. Plugin Loading Sequence
1.  **Bootstrap**: `main.py` initializes `CoreKernel`.
2.  **Discovery**: `PluginManager` scans `src/modules` and `entry_points`.
3.  **Registration & Auto-Discovery**:
    *   **Auto-Discovery**: Scans `router.py`, `models.py`, `admin.py` in module dirs.
    *   **Hooks**: Calls `hook.register_routes()` (custom overrides).
    *   **Wiring**: Mounts routers, collects Beanie documents, registers Admin pages.
4.  **Startup**: `Beanie.init_beanie()` called with all collected documents (Auto + Hook).
5.  **Server Start**: Uvicorn starts the app.

## 5. Technical Decisions & Trade-offs

| Component | Choice | Reason | Trade-off |
| :--- | :--- | :--- | :--- |
| **Web Framework** | **FastAPI** | High permornance, async native, auto-docs (Swagger). | Slightly higher learning curve than Flask/Django for beginners. |
| **UI Framework** | **NiceGUI** | Python-only frontend, reactive state, easy push updates. | Server-side state means higher memory usage per concurrent user compared to SPA/API. |
| **Database** | **MongoDB + Beanie** | Schema flexibility, async ODM, ease of cross-linking. | No ACID transactions across collections (though 4.0+ supports multi-doc transactions). |
| **Task Queue** | **TaskIQ** | Broker-agnostic, easy integration with FastAPI/Pydantic. | Less mature ecosystem than Celery, but more modern/async-friendly. |
| **Modularity** | **Pluggy** | Minimalist, used by Pytest, strict interface definitions. | Requires explicit hook definitions, less "magic" than simple introspection. |

## 6. Directory Structure

```text
repo_root/
├── src/
│   ├── core/              # Kernel code
│   │   ├── auth/          # User & Auth logic
│   │   ├── bus/           # Event Bus
│   │   ├── db/            # Base DB models & init
│   │   └── ui/            # Base UI kit & Layouts
│   ├── modules/           # Plugin directory
│   │   ├── admin/         # Core Admin Module
│   │   ├── storage/       # Storage Module (MinIO/S3/Local)
│   │   ├── cache/         # Caching Module (diskcache)
│   │   ├── inventory/     # Example Business Module
│   │   └── ...
│   └── main.py            # Entry point
├── docs/                  # Documentation
├── tests/                 # Pytest suite
└── pyproject.toml         # Dependencies & Tool config
```

## 7. Architectural Patterns
*   **Modular Monolith**: Single deployment, logical separation.
*   **Clean Architecture**: 
    *   **Entities** (Beanie Models) -> **Use Cases** (Services) -> **Interface Adapters** (Routers/UI).
*   **Event-Driven**: Decoupling modules via Event Bus.
*   **Hexagonal (Ports & Adapters)**:
    *   **Ports**: `DataSource` Protocol, `Service` Interfaces.
    *   **Adapters**: `S3DataSource`, `MongoRepository`.
