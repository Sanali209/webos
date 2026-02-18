# WebOS Framework Design Document

## 1. Introduction
The **WebOS Framework** is a modular, extensible, and scalable platform designed for building complex web-based internal tools and business applications. It prioritizes developer efficiency ("rad dev"), maintainability, and clean architecture through a plugin-based system.

## 2. Key Principles
*   **Inversion of Control (IoC)**: Modules are decoupled. They rely on the Core's abstractions and a central Event Bus rather than direct dependencies.
*   **Dependency Injection**: The Core injects services, data contexts, and configuration into modules, ensuring testability and isolation.
*   **Pluggability**: All functional extensions are modules managed by **Pluggy**. The core defines hooks; modules implement them.
*   **Syntactic Sugar**: The SDK provides high-level helpers (e.g., `self.add_table(data)`) to reduce boilerplate.
*   **Convention over Configuration**: Core auto-discovers standard module components (`router.py`, `models.py`, `admin.py`) to minimize wiring code.

## 3. Technology Stack
*   **Backend**: FastAPI (Web framework), TaskIQ (Async tasks), Httpx (Async HTTP client).
*   **Database**: MongoDB with **Beanie** (ODM).
*   **Frontend**: **NiceGUI** (Server-side rendering, separate state per client).
*   **Shell**: **Command Palette** (HUD) for unified "Shell in Shell" navigation.
*   **Modularity**: **Pluggy** (Plugin management).
*   **Authentication**: FastAPI Users (Security, User management).
*   **Visualization**: Plotly, Highcharts (via generic JS wrappers or NiceGUI integration).
*   **Data Layout**: **AG Grid** (Primary data explorer and bulk editor).
*   **Utilities**: Loguru (Logging), Pydantic (Validation & Settings), Cookiecutter (Scaffolding).

## 4. Core Architecture
The Core acts as the kernel, providing stability and foundational services to potentially unstable or rapidly changing modules.

### 4.1. Core SDK (Base Capabilities)
Modules inherit from base classes provided by the Core to ensure consistency.

*   **`BaseService`**:
```markdown
    *   Automatic dependency injection of core services and configuration.
    *   Access to the global Event Bus for inter-module communication.
```
    *   Built-in logging (Trace ID propagation).
    *   Standardized error handling and response formatting.
*   **`AccessControl`**:
    *   Decorators for method-level security: `@require_permission("inventory.read")`.
    *   Integration with Unified Auth.

*   **`Messenger`**:
    *   Unified notification interface.
    *   `self.notify.success("Operation complete")` -> Triggers NiceGUI toast/notification.

### 4.2. Inter-Module Communication
*   **Event Bus**:
    *   Asynchronous implementation (likely wrapping `asyncio` queues or a lightweight in-memory broker).
    *   Pattern: `bus.emit("entity:action", payload)` / `bus.subscribe("entity:action", handler)`.
    *   Modules communicate *intent* or *status* without knowing consumers.
*   **Data Injection**:
    *   Decorators to request access to other modules' data models safely.
    *   Example: An Analytics module requesting read-access to the Warehouse module's data.

## 5. Data Architecture
*   **Beanie ODM**: Primary data layer.
*   **Registry-Based Initialization**: The Core scans designated paths for classes inheriting from `CoreDocument`. These are automatically registered with Beanie on startup.
    *   Utilizes Beanie's `Link` for referencing documents across modules.
    *   Lazy-loading strategies (`fetch_links=True` only when needed) to prevent performance bottlenecks.
*   **Circular Dependency Management**:
    *   Use **String-based Type Resolution** (`Link["module.class_name"]`) to avoid import cycles.
    *   Strictly use `TYPE_CHECKING` blocks for type-only imports.
*   **Schema Evolution**:
    *   **Tool**: `beanie-migration`.
    *   **Structure**: `src/modules/<name>/migrations/`.
    *   **Process**: Core CLI runs pending migrations for all enabled modules on startup.

## 6. User Interface (NiceGUI)
*   **Slot System**:
    *   The Main Layout defines named slots (e.g., `sidebar_slot`, `dashboard_widget_slot`, `user_menu_slot`).
    *   Modules register widgets into these slots during startup.
*   **Theme Engine**:
    *   Centralized styling using TailwindCSS classes.
    *   The Core enforces a consistent color palette and typography.
*   **Auto-GUI SDK**:
    *   **AutoForm**: Generates UI forms directly from Pydantic models with validation.
    *   **DataExplorer**: Maps Beanie/Pydantic models to editable AG Grids for bulk management.
    *   Supports user isolation automatically for `OwnedDocument` types.

*   **Shell in Shell (The HUD)**:
    *   Unified **Command Palette** (`Ctrl+K`) for instant module navigation and search.
    *   Global hotkey listener integrated into the base layout.

## 7. Task System (TaskIQ)
*   **Background Processing**: Offloads long-running jobs (reports, data syncing).
*   **Helpers**:
    *   `BaseTask`: Wrapper for easy registration.
    *   `self.run_bg(func, *args)`: Fire-and-forget execution without complex broker setup for simple tasks.
*   **UI Integration**:
    *   Components to show task status (progress bars, spinners) using `Lottie-python` or native NiceGUI elements.
    *   Automatic notifications on task completion via the Messenger.

## 8. Security & Auth
*   **Unified Auth**: Single Sign-On (SSO) experience for all internal tools.
*   **User Object**: A `User` instance is injected into every request/session context.
*   **FastAPI Users**: Handles lifecycle (register, forgot password, verify) and token management (JWT).
*   **Default Admin**: System bootstraps with a configurable superuser if none exists.

## 9. Standard Modules

### 9.1. Extensible Admin Panel (System Management)
The Admin Panel is a host module that allows other modules to plug in their own management interfaces.

*   **Core Features**:
    *   **Dashboard**: Registry of widgets (CPU usage, active users, error rates).
    *   **User & Role Management**: RBAC configuration.
    *   **Module Manager**: List installed plugins, view status, enable/disable (if supported).
    *   **Settings Editor**: Unified interface powered by the **DataExplorer SDK** to edit persistent `ModuleSettingsDoc` configurations for all registered modules.
    *   **Logs Viewer**: Real-time log streaming from Loguru sinks.
*   **Extensibility**:
    *   Modules can register **Admin Pages** (e.g., `Inventory Settings`, `Audit Logs`).
    *   Modules can register **Dashboard Widgets**.
    *   **Hook**: `@hookspec def register_admin_ui(self, admin: AdminArea) -> None`.

### 9.2. Storage Module
*   **Abstract File System (AFS)**:
    *   Provides a unified, virtual file system hierarchy masking underlying storage details.
    *   **URN-based Addressing**: `fs://<datasource_id>/path/to/file`.
*   **Abstract Data Sources API**:
    *   **`DataSource` Interface**: Protocol for connecting to different storage providers (Local, S3, FTP, Google Drive, SMB).
    *   **Discovery**: Capability to list/discover available data sources and their contents.
    *   **Mount Points**: Mount data sources to virtual paths (e.g., `/mnt/s3_reports`).
*   **Backends**: Implementations for S3, MinIO, Local Disk, etc.
*   **Integration**:
    *   `self.storage.list_dir("fs://reports/")` -> Returns standard file objects.
    *   `self.storage.open("fs://reports/2023.pdf")` -> Returns async stream.

### 9.3. Caching Module
*   **Backend**: Powered by **diskcache** (SQLite-based, persistent, process-safe).
*   **Features**:
    *   **Memoization**: Decorator `@cache.memoize(expire=60)` for expensive function calls.
    *   **Key-Value Store**: Async API `await cache.set("config", data, expire=300)`.
    *   **Tagging**: Invalidate groups of keys `await cache.evict(tag="inventory")`.
*   **Use Cases**: API response caching, complex calculation results, session data.

## 10. Protocols & Contracts

### 10.1. Module Interface (Auto-Discovery & Hooks)
The system primarily uses **Auto-Discovery**. The **Pluggy Hooks** are reserved for advanced overrides.

*   **Auto-Discovery**:
    *   `src/modules/<name>/router.py` -> Auto-mounted as `/api/<name>`.
    *   `src/modules/<name>/models.py` -> `CoreDocument` subclasses auto-registered.
    *   `src/modules/<name>/admin.py` -> Auto-registered content for Admin Panel.

*   **Hooks (WebOSHookSpec)**:
    *   Used only when custom logic is needed during startup/shutdown or wiring.

```python
class WebOSHookSpec:
    @hookspec
    def register_routes(self, router: APIRouter) -> None:
        """(Optional) Manual route registration."""

    @hookspec
    def register_db_models(self) -> List[Type[CoreDocument]]:
        """Return a list of Beanie documents to register."""

    @hookspec
    def register_ui(self, layout: LayoutManager) -> None:
        """Register UI components into slots."""

    @hookspec
    def register_admin_ui(self, admin: AdminArea) -> None:
        """Register pages/widgets into the System Admin Panel."""
        
    @hookspec
    def register_settings(self) -> Type[BaseModel]:
        """Return a Pydantic model for module persistent settings."""

    @hookspec
    def startup(self, ctx: AppContext) -> Coroutine:
        """Async startup logic."""
```

### 10.2. Data Source Protocol
Any storage backend must implement this protocol to optionally support the AFS.

```python
class DataSource(Protocol):
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    
    async def list_dir(self, path: str) -> List[FileMetadata]:
        """Returns list of files/folders with metadata (size, mod_time)."""
        
    async def open_file(self, path: str, mode: str = "rb") -> AsyncBinaryIO:
        """Returns an async file-like object."""
        
    async def get_stat(self, path: str) -> FileMetadata: ...
```

### 10.3. Event Bus Contract
All events flow through the bus using a standardized envelope.

```python
@dataclass
class EventEnvelope:
    topic: str          # e.g., "users:created"
    payload: Dict       # The actual data
    source: str         # Module ID emitting the event
    trace_id: str       # For distributed tracing
    timestamp: float    # UTC timestamp
```

### 10.4. Context & User Protocol
Core injects a context object into every request/action.

```python
class User(Protocol):
    id: UUID
    username: str
    roles: List[str]
    permissions: Set[str]
    
    def has_permission(self, perm: str) -> bool: ...

@dataclass
class AppContext:
    user: User
    request_id: str
    session_id: str
    services: "ServiceRegistry"

### 10.5. Service Registry
Central point for dependency injection.

```python
    def register(self, name: str, service: Any) -> None: ...
```

## 11. Context Propagation Mechanism

To ensure seamless "Inter-Module Context Send", the system uses **Python ContextVars** and **Header Propagation**.

### 11.1. Local Execution (Async/Sync)
*   **Mechanism**: `contextvars` (Native Python).
*   **Behavior**: When Module A calls Module B directly, the `current_user` and `trace_id` are automatically available in Module B because they share the same asyncio task context.
*   **Implementation**:
    ```python
    # core/context.py
    ctx_user: ContextVar[User] = ContextVar("user")
    ctx_trace_id: ContextVar[str] = ContextVar("trace_id")
    ```

### 11.2. Event Driven (Event Bus)
*   **Mechanism**: Explicit Envelope Injection.
*   **Behavior**: When emitting an event, the Core automatically captures the current `contextvars` and injects them into the `EventEnvelope`.
*   **Flow**:
    1.  Module A emits `data:changed`.
    2.  Bus Middleware captures `ctx_user.get()` and `ctx_trace_id.get()`.
    3.  Bus creates `EventEnvelope(..., user_id=..., trace_id=...)`.
    4.  Consumer (Module B) receives envelope.
    5.  Bus Middleware *restores* values into `contextvars` before executing Module B's handler.

### 11.3. Background Tasks (TaskIQ)
*   **Mechanism**: TaskIQ Middleware.
*   **Behavior**: Similar to the Event Bus, context is serialized into the message headers.
*   **Result**: A background task running 5 minutes later still "knows" which user initiated it.

## 12. Business Process & Data Modeling

### 12.1. Data Modeling (MongoDB + Beanie)
*   **Audit Mixins**: All business entities inherit from `CoreDocument` which includes `created_at`, `updated_at`, `created_by`, `updated_by`.
*   **Soft Delete**: `deleted_at` field supported by default `BaseService` to prevent accidental data loss.
*   **Schema Separation**:
    *   **DB Model**: `class Order(CoreDocument): ...` (The database representation).
    *   **Pydantic Read**: `class OrderRead(BaseModel): ...` (Public API response).
    *   **Pydantic Write**: `class OrderCreate(BaseModel): ...` (Input validation).
*   **User Isolation (OwnedDocument)**:
    *   Mixin `OwnedDocument` automatically enforces `created_by == current_user` on queries if the user is not Admin.
    *   Simplifies multi-tenant/personal apps (e.g., Password Manager).

### 12.2. Business Logic Layer (Services)
*   **Stateless Services**: Logic resides in `Service` classes, not in API Routers or DB Models.
*   **Transaction Script Pattern**: For simple CRUD.
*   **Domain Model Pattern**: For complex logic, methods are on the domain objects, service orchestrates.
*   **State Management**:
    *   Use `enum.Enum` for Status fields (e.g., `Draft`, `Pending`, `Approved`).
    *   State transitions should be handled by specific Service methods (e.g., `approve_order()`) which emit events (`order:approved`).

### 12.3. Workflows (TaskIQ Orchestration)
For multi-step processes (e.g., "Import Data" -> "Process" -> "Notify"):
1.  **Chained Tasks**: `task1.kiq(result).call(task2)`
2.  **Sagas**: If a step fails, trigger a compensating transaction (undo previous steps).

## 13. Best Practices & Guidelines

### 13.1. Code Structure
*   **Keep Routers Thin**: Routers should only parse requests and call Services. No business logic in routers.
*   **Public vs Private Routers**:
    *   Split module API into `router_public.py` (Guest access) and `router_private.py` (Auth required).
    *   Simplifies permission management for apps like Blogs.
*   **Type Hinting**: 100% type coverage required. Use `mypy` in CI.
*   **Dependency Injection**: Always request services/repos via `ServiceRegistry` or `Pluggy` hooks. Never instantiate them manually in business logic.

### 13.2. Error Handling
*   **Custom Exceptions**: Throw domain-specific exceptions (e.g., `OrderNotFound`, `InsufficientFunds`) in Services.
*   **Global Exception Handler**: The Core captures these and converts them to standard HTTP 4xx/5xx responses.
*   **User Feedback**: Catch expected errors in UI triggers and show friendly Toast notifications.

### 13.3. Testing Strategy
*   **Unit Tests**: Test Services and Utils in isolation (mock DB and External APIs).
*   **Integration Tests**: Test Routers with a real (in-memory) MongoDB instance.
*   **E2E Tests**: Use Playwright to test critical NiceGUI flows.

### 13.4. Security
*   **Input Validation**: Rely on Pydantic.
*   **Output Sanitization**: Auto-escaped by NiceGUI/Jinja2.
*   **Least Privilege**: Modules should request only the data access they need.

### 13.5. Performance
*   **Async First**: All I/O (DB, Network, File) must be async.
*   **N+1 Problem**: Use `fetch_links=True` or manual aggregation. Avoid looping over queries.

*   **Caching**: Use `diskcache` for expensive computations or repeated external API calls.
*   **Rate Limiting**: Use `SlowAPI` to prevent "noisy neighbor" modules from monopolizing resources.

### 13.6. Operations
*   **Containerization**: Multi-stage Docker builds.
    *   Stage 1: Build UI assets (Node.js/Quasar).
    *   Stage 2: Install Python dependencies (Wheel build).
    *   Stage 3: Final runtime image (Distroless/Slim).

```

