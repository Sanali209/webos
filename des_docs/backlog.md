# Project Backlog

## Phase 0: Initialization & Repository Setup
- [x] **Repository Initialization**
    - [x] Initialize Git & .gitignore
    - [x] Clean root directory
- [x] **Dependency Management**
    - [x] Setup `pyproject.toml` (Poetry/Pipenv)
    - [x] Define Main & Dev dependencies
- [x] **Project Structure Creation**
    - [x] Create `src/core`, `src/modules`, `tests`, `docs`
    - [x] Add `__init__.py` files
- [x] **Quality Assurance Setup**
    - [x] Configure `pre-commit` (Black, Isort, Mypy)
    - [x] Create `.pre-commit-config.yaml`
- [x] **Environment Infrastructure**
    - [x] Create `docker-compose.yml` (Mongo, MinIO, Redis)
    - [x] Verify container connectivity
- [x] **Demonstration**: `scripts/demo_env.py` (Connect to backing services)
- [x] **Regression**: Run fresh `pytest` and `docker-compose ps`

## Phase 1: Core Kernel Foundation
- [x] **Configuration System**
    - [x] Implement `src/core/config.py` (Pydantic Settings)
    - [x] Support `.env` loading
- [x] **Structured Logging**
    - [x] Configure Loguru with JSON sink
    - [x] Implement Trace ID context propagation
- [x] **Service Registry (DI)**
    - [x] Implement Singleton Registry
    - [x] Define Registration/Retrieval methods
- [x] **Event Bus Engine**
    - [x] Implement `EventBus` (Subscribe/Emit)
    - [x] Define `EventEnvelope`
- [x] **Global Exception Handling**
    - [x] Create FastAPI middleware for exceptions
    - [x] Map domain errors to HTTP statuses
- [x] **Demonstration**: `scripts/demo_event_bus.py`
- [x] **Regression**: Run unit tests (Registry, EventBus)

## Phase 2: Data Layer & Authentication
- [x] **Database Initialization** (Motor/Beanie)
- [x] **Base Models & Mixins** (AuditMixin)
- [x] **Authentication Integration** (FastAPI Users)
- [x] **Permission System** (`@require_permission`)
- [x] **User Isolation Pattern** (`OwnedDocument` Mixin)
- [x] **Demonstration**: `scripts/demo_auth_flow.py`
- [x] **Regression**: Verify Auth + Event Bus tests

## Phase 3: Module System & Auto-Discovery
- [x] **Module Discovery Logic**
- [x] **Auto-Wiring** (Routes/Models)
- [x] **Pluggy Hooks**
- [x] **CLI Tools**
- [x] **Demonstration**: `src/modules/demo_hello_world/`
- [x] **Regression**: Full suite + new module loader tests

## Phase 4: UI Engine (NiceGUI)
- [x] **NiceGUI Integration**
- [x] **Slot-Based Layout System**
- [x] **Navigation & Menu**
- [x] **Theme Engine**
- [x] **Launchpad** (App Grid Component)
- [x] **Demonstration**: `src/modules/demo_dashboard/`
- [x] **Regression**: API Access + UI Playwright tests

## Phase 5: Storage & Caching
- [x] **Storage Protocol & Local Backend**
- [x] **Abstract File System (AFS)**
- [x] **S3 Backend**
- [x] **Caching Module** (DiskCache)
- [x] **Demonstration**: `scripts/demo_storage.py`
- [x] **Regression**: Verify I/O abstractions + previous tests

## Phase 6: Task System (TaskIQ)
- [x] **TaskIQ Setup**
- [x] **Context Propagation Middleware**
- [x] **Task UI Widget**
- [x] **Demonstration**: `src/modules/demo_report/`
- [x] **Regression**: Verify Async Task execution + Core integrity

## Phase 7: Extensible Admin & Polish
- [x] **Admin Dashboard Module**
- [x] **Extensible Inspector**
- [x] **Settings Editor**
- [x] **Security & Perf Review**
- [x] **Demonstration**: Complete System Demo (Admin Panel)
- [x] **Regression**: Final Full Suite Run (Zero Failures)

## Phase 8: Demonstration Ecosystem
- [ ] **Multi-Portal Landing (Shell)**
    - [ ] App Grid / Launchpad UI
- [ ] **App 1: Blogger Portal**
    - [ ] CRUD Posts, Rich Text Editor
    - [ ] Public View
- [ ] **App 2: Dual-Panel File Explorer**
    - [ ] AFS Integration (Local/S3)
    - [ ] Drag & Drop Interface
- [ ] **App 3: Personal Password Manager**
    - [ ] User Isolation (Row Level Security)
    - [ ] Encryption Demonstration
- [ ] **Integration Workflows**
    - [ ] Cross-module (Blog -> File Picker)
- [ ] **Demonstration**: Recorded Walkthrough of all 3 apps

## Phase 9: Unified Shell & Command Palette
- [ ] **Command Palette (HUD)**: `Ctrl+K` Navigation
- [ ] **System Shell**: Dashboard log widget
- [ ] **UX Polish**: Unified navigation consistency audit

---

## Knowledge Log
> Record key learnings, decisions, and technical details here.

*   **2026-02-17**: Initial Project Plan created.
*   **2026-02-17**: Phase 0 & 1 Completed.
    *   *Decision*: Moved Redis host port to `6380` due to local conflict on `6379`.
    *   *Issue*: Mongo authentication in `demo_env.py` requires `?authSource=admin` even if root credentials are provided.
    *   *Tip*: Use `python -m pytest` for reliable module discovery in complex structures.
*   **2026-02-17**: Phase 2 Completed.
    *   *Decision*: MongoDB authentication was disabled for Dev environment to avoid Windows-specific credential negotiation issues.
    *   *Fix*: `BeanieBaseUser` in `fastapi-users-db-beanie` 5.0 is NOT a generic; use `BeanieBaseUserDocument` as base instead.
    *   *Dependency*: Added `fastapi-users-db-beanie` to `pyproject.toml`.
*   **2026-02-17**: Phase 3 Completed (Module System).
    *   *System*: Implemented `ModuleLoader` using `pluggy` for hook-based extensibility.
    *   *Convention*: Support for auto-discovery of `models.py` (Beanie) and `router.py` (FastAPI).
    *   *Fix*: Refactored `main.py` to use a central `api_router` to ensure all module routes respect `API_PREFIX`.
    *   *Issue*: Encountered race condition in `lifespan`; moved module discovery to top-level to ensure models are registered before DB init.
    *   *Tool*: Created `scripts/test_loading.py` to verify module integration without starting full server.
*   **2026-02-17**: Phase 4 Completed (UI Engine).
    *   *System*: Integrated NiceGUI with FastAPI. Implemented slot-based layout for dynamic extension.
    *   *Registry*: Created `UIRegistry` to track registered apps and menu items for the Launchpad and Sidebar.
    *   *Fix*: Corrected `demo_auth_flow.py` and other scripts to respect `API_PREFIX` (/api).
*   **2026-02-17**: Phase 5 Completed (Storage & Caching).
    *   *Architecture*: Implemented `AFSManager` for unified URN-based file access (`fs://local/...`).
    *   *Fix*: Standardized `WebOSHookSpec` to remove `self` from signatures, allowing standalone functions in module files (e.g., `hooks.py`) to match correctly.
    *   *Dependency*: Added `aioboto3`, `diskcache`, and `aiofiles`.
    *   *Loader*: Refactored `ModuleLoader` to support dynamic hook registration via `SimpleNamespace` factory for auto-discovery plugins.
*   **2026-02-17**: Phase 6 Completed (Task System).
    *   *Broker*: Integrated TaskIQ with `ListQueueBroker` and Redis.
    *   *Context*: Implemented `ContextPropagationMiddleware` to pass `user_id` and `trace_id` to workers via message labels.
    *   *Fix*: Corrected TaskIQ internal class naming (e.g., `TaskiqEvents` instead of `TaskIQEvents`) and fixed argument names in `RedisAsyncResultBackend` (e.g., `redis_url`).
    *   *UI*: Created `TaskProgressWidget` for real-time (polling) status updates in NiceGUI.
    *   *Integration*: Added `set_task_context` dependency to captured authenticated users in the request cycle.
*   **2026-02-17**: Phase 7 Completed...
*   **2026-02-18**: Phase 8 Execution & Debugging.
    *   *System*: Resolved `PydanticSerializationError` in TaskIQ middleware by removing non-serializable lambdas from `ContextVar` defaults.
    *   *UI*: Fixed `AttributeError` by switching from `ui.storage` to `app.storage` for NiceGUI session persistence (NiceGUI v2.x).
    *   *UI*: Resolved closure capture bug in Launchpad where all app cards triggered the same route; used `lambda a=app: ...` to lock the iteration variable.
    *   *System*: Implemented `setup_default_user` in `lifespan` for conditional database seeding (creates `admin@webos.io` only if no users exist).
    *   *Convention*: Centralized `user_id_context` in `src/core/middleware.py` to prevent cross-module inconsistencies.
