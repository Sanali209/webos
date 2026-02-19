# WebOS Framework Roadmap

## Phase 0: Initialization & Repository Setup
**Goal**: Establish a reproducible development environment, project structure, and automated quality checks to ensure a solid foundation for the "Standard Module" system.

*   **Subtasks**:

    *   [x] **Repository Initialization**
        *   **Subtask**: Initialize Git, create `.gitignore` (Python/Node/Docker), and set up the root directory.
        *   **Implementation Goal**: A clean repository that ignores unnecessary files (`__pycache__`, `node_modules`, `.env`) and has a clear root structure.
        *   **Testing**: Run `git status` to verify no ignored files are tracked.
        *   **Notes**: Use `github/gitignore` templates for Python and Node.

    *   [x] **Dependency Management**
        *   **Subtask**: Setup `poetry` or `pipenv` with `pyproject.toml`. Define groups: `main` (FastAPI, NiceGUI, Beanie), `dev` (Black, Isort, Mypy, Pytest).
        *   **Implementation Goal**: Reproducible dependency resolution. `poetry install` should set up the entire env.
        *   **Testing**: Run `poetry install` in a fresh container; verify `python -c "import fastapi"` works.
        *   **Notes**: Pin major versions to avoid breaking changes.

    *   [x] **Project Structure Creation**
        *   **Subtask**: Create `src/core`, `src/modules`, `tests`, `docs`, `scripts`. Add `__init__.py` where needed.
        *   **Implementation Goal**: Logical separation of Kernel (Core) and Plugins (Modules).
        *   **Testing**: Verify `import src.core` works from root.

    *   [x] **Quality Assurance Setup**
        *   **Subtask**: Configure `pre-commit` hooks for Black, Isort, Flake8, and Mypy. Create `.pre-commit-config.yaml`.
        *   **Implementation Goal**: Enforce coding standards automatically before commit.
        *   **Testing**: Try to commit malformatted code; verify hook fails and auto-fixes.

    *   [x] **Environment Infrastructure**
        *   **Subtask**: Create `docker-compose.yml` for MongoDB (4.0+), MinIO (S3 compatible), and Redis (TaskIQ broker).
        *   **Implementation Goal**: One command (`docker-compose up -d`) to start all backing services.
        *   **Testing**: Connect to Mongo via Compass, MinIO via Browser (9000), Redis via CLI.

    *   [x] **Demonstration Sample**
        *   **Subtask**: Create `scripts/demo_env.py` that connects to Mongo and Redis and prints "System Ready".
        *   **Goal**: Verify the entire stack is talking to each other.

    *   [x] **Regression Check**
        *   **Subtask**: Run `pytest` (should be empty but pass) and `docker-compose ps` to ensure stability.

*   **Phase Completion & Documentation**:
    *   [x] **Update Backlog**: Move Phase 0 items to Done in `Docs/backlog.md` with a summary of setup versions.
    *   [x] **Generate Documentation**: Create `README.md` (Setup Guide) and `CONTRIBUTING.md` (Style Guide).
    *   [ ] **Tutorial**: Write `Docs/tutorial/getting_started.md`: "How to go from Zero to Running Environment".
    *   [x] **Knowledge Capture**: Record selected versions (Python 3.11+, Mongo 6.0) in `Docs/knowledge/stack_decisions.md`.
    *   [x] **Self Check**: Verify a fresh clone + `docker-compose up` + `poetry install` results in a working ready-to-code state.

---

## Phase 1: Core Kernel Foundation
**Goal**: Build the "Spine" of the application (Dependency Injection, Event Bus, Configuration) to support the Modular Monolith architecture.

*   **Subtasks**:

    *   [x] **Configuration System**
        *   **Subtask**: Implement `src/core/config.py` using `pydantic-settings`. Support `.env` file loading.
        *   **Implementation Goal**: Type-safe access to config (e.g., `settings.mongo_dsn`).
        *   **Testing**: Create a test that overrides env vars and verifies settings update.
        *   **Notes**: Use `model_config = SettingsConfigDict(env_file=".env")`.

    *   [x] **Structured Logging**
        *   **Subtask**: Configure `Loguru` to intercept standard logging. Add JSON sink for production.
        *   **Implementation Goal**: Unified logging format with Trace IDs using `contextvars`.
        *   **Testing**: Emit a log; verify Trace ID is present in output.

    *   [x] **Service Registry (DI)**
        *   **Subtask**: Implement `ServiceRegistry` singleton. Methods: `register(interface, implementation)`, `get(interface)`.
        *   **Implementation Goal**: Decouple interface from implementation (e.g., test mocks vs real DB).
        *   **Testing**: Register a MockService, retrieve it, and assert identity.
        *   **Notes**: Keep it simple; avoid complex auto-wiring magic for now.

    *   [x] **Event Bus Engine**
        *   **Subtask**: Implement `EventBus` with `subscribe` and `emit` methods. Define `EventEnvelope` dataclass.
        *   **Implementation Goal**: Decoupled module communication. Async execution of handlers.
        *   **Testing**: Publish "test:event"; verify subscriber received payload + context.
        *   **Notes**: Ensure exception safety (one subscriber failing shouldn't crash the bus).

    *   [x] **Global Exception Handling**
        *   **Subtask**: Create FastAPI `exception_handler` middleware. Map domain exceptions to HTTP status codes.
        *   **Implementation Goal**: API never returns 500 HTML to client; always JSON `{"error": "..."}`.
        *   **Testing**: Raise a custom `EntityNotFound`; verify HTTP 404 response.

    *   [x] **Demonstration Sample**
        *   **Subtask**: Create `scripts/demo_event_bus.py`.
        *   **Code**: Simulates a service emitting an event and another service reacting to it via the Bus.
        *   **Goal**: visual proof of the Observer pattern working.

    *   [x] **Regression Check**
        *   **Subtask**: Run `pytest`. Ensure configuration, logging, and registry tests all pass.

*   **Phase Completion & Documentation**:
    *   [x] **Update Backlog**: Mark Phase 1 tasks done. Log any architectural changes.
    *   [ ] **Generate Documentation**: Create `Docs/core/architecture.md` detailing the Event Bus and DI patterns.
    *   [ ] **Tutorial**: Add "How to use the Event Bus" example in `Docs/tutorial/core_concepts.md`.
    *   [ ] **Knowledge Capture**: Document "Why ContextVars?" and DI trade-offs.
    *   [x] **Self Check**: Can I start the generic FastAPI app and see clean JSON logs?

---

## Phase 2: Data Layer & Authentication
**Goal**: Implement secure data persistence with MongoDB/Beanie and User Management.

*   **Subtasks**:

    *   [x] **Database Initialization**
        *   **Subtask**: Setup `Motor` client and `Beanie` init checks in `lifespan` event.
        *   **Implementation Goal**: Async DB connection established on startup.
        *   **Testing**: access endpoint `/health` which pings DB.

    *   [x] **Base Models & Mixins**
        *   **Subtask**: Create `CoreDocument(Document)` with `AuditMixin` (`created_at`, `updated_at`).
        *   **Implementation Goal**: Automatic timestamping and user tracking on save.
        *   **Testing**: Save a doc; assert `created_at` is populated.

    *   [x] **Authentication Integration**
        *   **Subtask**: Integrate `fastapi-users` with Beanie adapter. Setup `User`, `UserCreate`, `UserRead` models.
        *   **Implementation Goal**: Standard JWT/Cookie auth flow (Login/Register/Logout).
        *   **Testing**: `POST /auth/login` returns valid token.

    *   [x] **Permission System**
        *   **Subtask**: Implement `@require_permission("scope")` dependency.
        *   **Implementation Goal**: Fine-grained RBAC at the route level.
        *   **Testing**: Access protected route without permission -> 403; With permission -> 200.
        *   **Notes**: Store permissions as a list of strings in User model or Role model.

    *   [x] **User Isolation Pattern**
        *   **Subtask**: Implement `OwnedDocument` mixin.
        *   **Logic**: Override `find()` to automatically append `{"created_by": ctx_user.id}`.
        *   **Goal**: Zero-effort data isolation for "Personal" modules (Vault, Notes).

    *   [x] **Demonstration Sample**
        *   **Subtask**: Create `scripts/demo_auth_flow.py`.
        *   **Code**: Script that registers a user programmatically, logs in to get a token, and calls a protected API.
        *   **Goal**: Verify Auth+DB+Permissions loop.

    *   [x] **Regression Check**
        *   **Subtask**: Run all tests. Verify Phase 1 (Event Bus) still works alongside the new DB layer.

*   **Phase Completion & Documentation**:
    *   [x] **Update Backlog**: Report on Auth implementation details.
    *   [ ] **Generate Documentation**: `Docs/core/auth_system.md` (RBAC model).
    *   [ ] **Tutorial**: "How to protect a route" guide.
    *   [x] **Self Check**: Can I register a user, login, and access a protected endpoint?

---

## Phase 3: Module System & Auto-Discovery
**Goal**: Implement the "Convention over Configuration" plugin system for Rad Dev.

*   **Subtasks**:

    *   [x] **Module Discovery Logic**
        *   **Subtask**: Create `ModuleLoader` to scan `src/modules/*`.
        *   **Implementation Goal**: Automatically find list of available module packages.
        *   **Testing**: Create dummy folder `src/modules/testmod`; verify loader finds it.

    *   [x] **Auto-Wiring (Routes & Models)**
        *   **Subtask**: using `importlib`, try import `router.py`, `models.py`, `admin.py`. If found, register them.
        *   **Implementation Goal**: Zero-config module loading. Just create files, and they work.
        *   **Testing**: Add `router.py` to `testmod`; verify endpoint shows up in Swagger UI.

    *   [x] **Pluggy Hooks (Advanced)**
        *   **Subtask**: Define `WebOSHookSpec` for manual overrides (`startup`, `shutdown`).
        *   **Implementation Goal**: Allow modules to run complex logic on boot.
        *   **Testing**: Implement a startup hook that logs a message; verify log appears.

    *   **CLI Tools**
        *   **Subtask**: Implement `python main.py modules list`.
        *   **Implementation Goal**: debugging tool to see what is loaded.
        *   **Testing**: detailed output of loaded modules and their status.

    *   **Demonstration Sample**
        *   **Subtask**: Create `src/modules/demo_hello_world/` structure.
        *   **Code**: A functional module with 1 Route, 1 Model, and 1 Event Listener.
        *   **Goal**: Prove the "Rad Dev" concept works as designed.

    *   **Regression Check**
        *   **Subtask**: Run full test suite. Ensure adding the new module loader didn't break core auth or DB connections.

*   **Phase Completion & Documentation**:
    *   [x] **Update Backlog**: Phase 3 items done.
    *   [ ] **Generate Documentation**: `Docs/core/module_system.md` (Folder structure, Auto-discovery rules).
    *   [ ] **Tutorial**: `Docs/tutorial/create_first_module.md` (Step-by-step Hello World).
    *   [x] **Self Check**: Can I create a new module partition without touching `src/core` or `main.py`?

---

## Phase 4: UI Engine (NiceGUI & Layouts)
**Goal**: Create the visual Shell and UI Component system.

*   **Subtasks**:

    *   [x] **NiceGUI Integration**
        *   **Subtask**: Mount `ui.run_with(fastapi_app)`. Handle static file serving.
        *   **Implementation Goal**: Serve UI at root `/` or `/ui`.
        *   **Testing**: Access `localhost:8000/` and see "Hello NiceGUI".

    *   [x] **Slot-Based Layout System**
        *   **Subtask**: Create `MainLayout` class with `add_slot("name", component)`.
        *   **Implementation Goal**: Modules can inject widgets into Sidebar/Header without editing Layout code.
        *   **Testing**: Module A adds button to Sidebar; Module B adds avatar to Header. Both appear.

    *   [x] **Navigation & Menu**
        *   **Subtask**: Implement dynamic Sidebar menu based on registered Module pages.
        *   **Implementation Goal**: Auto-generated menu from Module metadata.
        *   **Testing**: Create module with `menu_name="Inventory"`; verify item appears in Drawer.

    *   [x] **Theme Engine**
        *   **Subtask**: Define Color Palette and Typography classes (Tailwind wrappers).
        *   **Implementation Goal**: Consistent look & feel. Easy Dark Mode toggle.
        *   **Testing**: Switch theme; verify colors change globally.

    *   [x] **Launchpad (App Grid)**
        *   **Subtask**: Create `AppCard` component and `LaunchpadLayout`.
        *   **Implementation Goal**: Standard UI for the "Multi-Portal" entry point.
        *   **Testing**: Render grid of dummy apps.

    *   [x] **Demonstration Sample**
        *   **Subtask**: Create `src/modules/demo_dashboard/`.
        *   **Code**: A module that injects a "Sales Chart" widget into the Main Dashboard slot.
        *   **Goal**: Visually confirm the Layout/Slot system works.

    *   **Regression Check**
        *   **Subtask**: check that API endpoints (Swagger) still work alongside the new UI. Run Playwright UI tests.

*   **Phase Completion & Documentation**:
    *   [ ] **Update Backlog**: Phase 4 done.
    *   [ ] **Generate Documentation**: `Docs/ui/layout_system.md` ( Slots, Theming).
    *   [ ] **Tutorial**: "How to add a Page and Menu Item".
    *   [ ] **Self Check**: Does the shell resize correctly on mobile? Do slots work?

---

## Phase 5: Storage & Caching
**Goal**: Abstract I/O operations for Files and Expensive Computations.

*   **Subtasks**:
    *   [x] **Storage Protocol & Local Backend**
        *   **Subtask**: Define `DataSource` protocol. Implement `LocalDataSource` (`./data/storage`).
        *   **Implementation Goal**: Standard API (`open`, `save`, `list`) for file ops.
        *   **Testing**: Save file via API; check physical existence on disk.
    *   [x] **Abstract File System (AFS)**
        *   **Subtask**: Implement URN resolver `fs://<source>/<path>`.
        *   **Implementation Goal**: Uniform addressing regardless of backend.
        *   **Testing**: User resolves `fs://local/doc.pdf`.
    *   [x] **S3 Backend**
        *   **Subtask**: Implement `S3DataSource` using `boto3`/aioboto3.
        *   **Implementation Goal**: Seamless switch to MinIO/AWS S3.
        *   **Testing**: Upload file to `fs://s3/`; verify in MinIO Console.
    *   [x] **Caching Module**
        *   **Subtask**: Integrate `diskcache`. Add `@cache.memoize` decorator.
        *   **Implementation Goal**: Persistent caching surviving restarts.
        *   **Testing**: Memoize timestamp function; call twice; assert same result.
    *   [x] **Demonstration Sample**
        *   **Subtask**: Create `scripts/demo_storage.py`.
        *   **Code**: Script that uploads a file to S3 via AFS, clears the local cache, and downloads it again.
        *   **Goal**: Verify I/O abstractions.
    *   [x] **Regression Check**
        *   **Subtask**: Verify Core, Auth, Modules, and UI still function. Ensure Caching doesn't introduce staleness bugs.
*   **Phase Completion & Documentation**:
    *   [x] **Update Backlog**: Phase 5 done.
    *   [x] **Generate Documentation**: `Docs/modules/storage.md` and `Docs/modules/caching.md`.
    *   [ ] **Tutorial**: "How to upload and serve a file".
    *   [x] **Self Check**: Can I switch from Local to S3 storage via config, without code changes?

---

## Phase 6: Task System (TaskIQ)
**Goal**: Robust background processing for long-running operations.

*   **Subtasks**:
    *   [x] **TaskIQ Setup**
        *   **Subtask**: Configure Broker (Redis) and Result Backend. Initialize `TaskIQ-FastAPI`.
        *   **Implementation Goal**: Async task execution outside request cycle.
        *   **Testing**: Trigger task via HTTP; verify execution in worker logs.
    *   [x] **Context Propagation Middleware**
        *   **Subtask**: Create middleware to grab `contextvars` (User, TraceID) and inject into Task headers.
        *   **Implementation Goal**: Tasks know *who* triggered them.
        *   **Testing**: Task logs `current_user.id`; verify it matches triggering user.
    *   [x] **Task UI Widget**
        *   **Subtask**: Create NiceGUI widget polling Task status (Progress bar).
        *   **Implementation Goal**: Real-time feedback for users.
        *   **Testing**: Start long task; watch progress bar update to 100%.
    *   [x] **Demonstration Sample**
        *   **Subtask**: Create `src/modules/demo_report/`.
        *   **Code**: A module with a "Generate PDF" button that triggers a background task and shows a progress bar.
        *   **Goal**: End-to-end verification of async workflows.
    *   [x] **Regression Check**
        *   **Subtask**: Ensure adding TaskIQ middleware didn't break standard request context. Run all tests.
*   **Phase Completion & Documentation**:
    *   [x] **Update Backlog**: Phase 6 done.
    *   [x] **Generate Documentation**: `Docs/core/background_tasks.md`.
    *   [ ] **Tutorial**: "How to create a background report generator".
    *   [x] **Self Check**: Does a failed task log an error and show "Failed" in UI?

---

## Phase 7: Extensible Admin & Final Polish
**Goal**: System Management interface and production readiness.

*   **Subtasks**:
    *   [x] **Admin Dashboard Module**
        *   **Subtask**: Create `src/modules/admin`. Register itself via standard auto-discovery.
        *   **Implementation Goal**: "Dogfooding" the module system.
        *   **Testing**: `/admin` route loads dashboard.
    *   [x] **Extensible Inspector**
        *   **Subtask**: Add `register_admin_panel` hook support. Implement User Manager & Module Manager.
        *   **Implementation Goal**: Manage Users and Plugins from UI.
        *   **Testing**: Create new user via Admin UI; Disable a test module.
    *   [x] **Settings Editor**
        *   **Subtask**: UI to reflect and edit `pydantic-settings`.
        *   **Implementation Goal**: Change log level via UI.
        *   **Testing**: Update setting; verify app behavior change.
    *   [x] **Final Security & Perf Review**
        *   **Subtask**: Run security audit (bandit). Profile load times.
        *   **Implementation Goal**: Secure, performant release candidate.
    *   [x] **Demonstration Sample**
        *   **Subtask**: `Complete System Demo`.
        *   **Code**: The entire Admin panel acts as the final "sample" of the framework's capabilities.
        *   **Goal**: Comprehensive showcase.
    *   [x] **Regression Check**
        *   **Subtask**: **Final Full Suite Run**. Run every unit, integration, and E2E test. Zero failures allowed.
*   **Phase Completion & Documentation**:
    *   [x] **Update Backlog**: All phases done.
    *   [x] **Generate Documentation**: `Docs/guide/admin_manual.md`.
    *   [ ] **Tutorial**: "Full System Walkthrough".
    *   [x] **Knowledge Capture**: "Lessons Learned" retrospective.
    *   [x] **Self Check**: Is the system "Module Ready"? Can I extract a business module to a separate repo and install it?

---

## Phase 8: Demonstration Ecosystem (The "OS" Experience)
**Goal**: Validate the framework's versatility by building three distinct "Real World" applications that coexist in the Shell.

*   **Subtasks**:

    *   **Multi-Portal Landing (The Shell)**
        *   **Subtask**: Implement `LaunchpadLayout` (created in Phase 4). Register apps via `register_ui(layout)`.
        *   **Implementation Goal**: Populated "Start Menu".
        *   **Testing**: Click "Blogger" icon -> Redirects to `/blogger` within the shell.

    *   **App 1: Blogger Portal (Content Management)**
        *   **Subtask**: Create `src/modules/blogger`. Use `Public vs Private` router pattern.
        *   **Implementation Goal**: Guest can read (`router_public`), User can write (`router_private`).
        *   **Testing**: Create post as Admin; View post as Guest.

    *   **App 2: Dual-Panel File Explorer (System Tool)**
        *   **Subtask**: Create `src/modules/file_commander`. Use `DataSource` API directly.
        *   **Implementation Goal**: Stress-test AFS.
        *   **Testing**: Move file from `fs://local/tmp` to `fs://s3/backup` using UI buttons.

    *   **App 3: Personal Password Manager (Security Tool)**
        *   **Subtask**: Create `src/modules/vault`. Inherit models from `OwnedDocument`.
        *   **Implementation Goal**: Verify `OwnedDocument` prevents User A from seeing User B's secrets without extra code.
        *   **Testing**: Create secret; Login as different user; Verify secret is invisible.

    *   **Integration & workflows**
        *   **Subtask**: specific cross-module interaction.
        *   **Implementation Goal**: "Attach file from File Explorer to a Blog Post".
        *   **Testing**: Open Blog Editor -> Click "Select Image" -> Opens File Picker (Mini File Explorer).

    *   **Demonstration Sample**
        *   **Subtask**: **Full Ecosystem Walkthrough Video**.
        *   **Goal**: Record a continuous session: Login -> Launch Files -> Upload Image -> Launch Blogger -> Write Post using Image -> Log out.

    *   **Regression Check**
        *   **Subtask**: Ensure running 3 complex modules doesn't degrade performance (check RAM usage).


---

## Phase 9: Unified Shell & Command Palette
**Goal**: Unify the "OS" experience by providing a centralized command/terminal interface and cross-module navigation HUD.

*   **Subtasks**:

    *   **Command Palette (HUD)**
        *   **Subtask**: Implement `CommandPalette` dialog in `src/ui/layout.py`. Register `Ctrl+K` global hotkey.
        *   **Implementation Goal**: Searchable indexed commands and apps.
        *   **Testing**: `Ctrl+K` -> type "Blogger" -> Enter -> Navigates.

    *   **System Shell Widget**
        *   **Subtask**: Create a "Terminal" widget that shows real-time system logs or simple shell outputs.
        *   **Implementation Goal**: Provide "Standard Module" for system-wide status.
        *   **Testing**: View logs in dashboard widget while performing actions.

    *   **Unified Navigation Audit**
        *   **Subtask**: Review all modules to ensure they use Sidebar and Header slots correctly.
        *   **Implementation Goal**: 100% consistency across the ecosystem.

*   **Phase Completion & Documentation**:
    *   [x] **Final Retrospective**: "The Modular Monolith: Practical Lessons".
    *   [x] **Documentation**: Full API guide for "Built-in Shell" extensions.
1.  
---

## Phase 10: Auto-GUI SDK & Persistent Core Refinement
**Goal**: Elevate the Framework's developer experience by automating UI generation and providing robust module configuration.

*   **Subtasks**:

    *   **Auto-GUI SDK (DataExplorer)**
        *   **Subtask**: Implement Type Mapping Engine.
            *   *Detail*: Map `str`, `int`, `bool`, `datetime`, and `Enum` to AG Grid `columnDefs`.
        *   **Subtask**: Implement `DataExplorer` core component.
            *   *Detail*: Wrapper for `ui.aggrid` with support for both `Iterable[BaseModel]` (in-memory) and `Type[Document]` (Beanie).
        *   **Subtask**: Implement Beanie Integration & User Isolation.
            *   *Detail*: Automatic filtering for `OwnedDocument` and real-time `on_cell_change` DB updates.
        *   **Automated Tests**:
            *   `test_mapping_engine`: Verify correct `columnDefs` generation for various Pydantic types.
            *   `test_beanie_crudes`: Verify grid-driven MongoDB updates and owner isolation.
        *   **Regression Tests**:
            *   Verify `Vault` and `File Explorer` stability during UI refactoring.

    *   **Persistent Module Settings**
        *   **Subtask**: Extend Hook System.
            *   *Detail*: Add `register_settings` to `WebOSHookSpec`.
        *   **Subtask**: Implement `SettingsService`.
            *   *Detail*: Logic to fetch from `system_settings` collection, merge with defaults, and cache in memory.
        *   **Subtask**: Real-time Sync.
            *   *Detail*: Emit Event Bus signals on setting updates.
        *   **Automated Tests**:
            *   `test_settings_loading`: Verify default vs DB priority.
            *   `test_settings_bus_emit`: Verify event notification on change.
        *   **Regression Tests**:
            *   Ensure `config.py` (env vars) is NOT overwritten by module settings.

    *   **Admin HUD Refinement**
        *   **Subtask**: Create Settings Explorer.
            *   *Detail*: Registry-style UI in Admin module listing all module settings.
        *   **Subtask**: DataExplorer Integration.
            *   *Detail*: Use the new SDK to render the editable settings grid.
        *   **Automated Tests**:
            *   `test_admin_settings_rendering`: Verify all module tabs appear correctly.
        *   **Regression Tests**:
            *   Verify Admin Dashboard widget slots remain functional.

*   **Phase Completion & Documentation**:
    *   [ ] **Generate Documentation**: `Docs/sdk/data_explorer.md` and `Docs/core/module_settings.md`.
    *   [ ] **Tutorial**: "Creating a Settings-Powered Module in 5 Minutes".

---

## Phase 11: Digital Asset Management (DAM)
**Goal**: Create a rich media library on top of the Abstract File System (AFS) to manage images, documents, and videos with metadata.

*   **Subtasks**:
    *   **DAM Module Foundation**
        *   **Subtask**: Create `src/modules/dam`. Defining `Asset` model with metadata fields.
        *   **Implementation Goal**: Database schema for tracking files managed by AFS.
    *   **Asset Ingestion**
        *   **Subtask**: Implement Upload Service using `AFS` backend.
        *   **Implementation Goal**: Upload file -> Save to S3/Local -> Create DB Record.
    *   **Visual Processing**
        *   **Subtask**: Implement `ThumbnailGenerator` service (Pillow).
        *   **Implementation Goal**: Auto-generate preview images for gallery view.
    *   **UI - Asset Gallery**
        *   **Subtask**: Build NiceGUI Gallery component with Grid View, Search, and Filtering.
        *   **Implementation Goal**: "Google Photos" style interface.
    *   **Integration**
        *   **Subtask**: Create `AssetPicker` widget.
        *   **Implementation Goal**: Allow other modules (e.g., Blog) to select assets seamlessly.
