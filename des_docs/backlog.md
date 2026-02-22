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

## Phase 10: Auto-GUI SDK & Persistent Core
- [ ] **Auto-GUI SDK (DataExplorer)**
    - [ ] Type Mapping Engine (Pydantic -> AG Grid)
    - [ ] Beanie CRUD Adapter
    - [ ] Pydantic List Wrapper (In-memory)
    - [ ] User Isolation (OwnedDocument check)
    - [ ] Automated Tests: Mapping & DB Sync
- [ ] **Persistent Settings Engine**
    - [ ] `register_settings` Hook implementation
    - [ ] `SettingsService` (Load/Save/Cache)
    - [ ] `system_settings` Collection migration
    - [ ] Event Bus signal on update
    - [ ] Automated Tests: Priority & Events
- [ ] **Admin Settings Explorer**
    - [ ] Explorer UI in Admin module
    - [ ] DataExplorer integration for settings list
- [ ] **Regression Suite**
    - [ ] Verify core boot sequence
    - [ ] Verify existing module integrity

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

---

## Phase 11: DAM — Framework Preparation
> Detail: `des_docs/design/dam/dam_roadmap.md` Phase 1
- [x] **1.1** Add Qdrant `v1.9.2` to `docker-compose.yml` (REST :6333, gRPC :6334, `qdrant_data` volume) ✅ Done
- [x] **1.2** DAM env vars in `src/core/config.py` (`QDRANT_URL`, `DAM_AI_ENABLED`, thresholds, paths)
- [x] **1.3** 7 new hookspecs in `src/core/hooks.py` (`register_services`, `on_startup_async`, `register_pipeline_processors`, `register_asset_drivers`, `register_asset_types`, `register_vector_definitions`, `register_page_slots`)
- [x] **1.4** Wire new hooks in `src/core/module_loader.py` + `main.py` lifespan
- [x] **1.5** Open slot registration in `src/ui/layout.py` (`UI_Slot` + `asset_picker_overlay` builtin)
- [x] **1.6** Create `src/ui/page_slot_registry.py` (`PageSlotRegistry` singleton)
- [x] **1.7** Add `badge_text`, `keyboard_shortcut` to `AppMetadata` in `src/ui/registry.py`
- [x] **1.8** Add `get_typed()` to `src/core/services/settings_service.py`
- [x] **Regression**: Full suite — existing modules unaffected, startup time delta < 200 ms

## Phase 12: DAM — Asset Model
> Detail: `des_docs/design/dam/dam_roadmap.md` Phase 2
- [x] **2.1** Module package skeleton (`src/modules/dam/` + all sub-folders)
- [x] **2.2** `Asset` Beanie model with all fields + compound text index
- [x] **2.3** `DetectedObject` sub-model (bbox 0–1 normalized, confidence validation)
- [x] **2.4** `Link` Beanie model + compound indexes
- [x] **2.5** `Album` Beanie model (OwnedDocument, user isolation)
- [x] **Regression**: MongoDB collections + indexes created on startup

## Phase 13: DAM — Asset Type System
> Detail: `des_docs/design/dam/dam_roadmap.md` Phase 3
- [x] **3.1** `AssetTypeDefinition` base class
- [x] **3.2** 5 built-in type implementations
- [x] **3.3** `AssetTypeRegistry` singleton
- [x] **3.4** `DAMHooks.register_asset_types` + `on_startup_async` pipeline
- [x] **Regression**: CRUD capabilities stableo/quicktime").type_id == "video"`

## Phase 14: DAM — Asset Drivers
> Detail: `des_docs/design/dam/dam_roadmap.md` Phase 4
- [x] **4.1** Abstract `BaseAssetDriver` class
- [x] **4.2** ImageDriver (Pillow, orientation, EXIF, GPS decoding)
- [x] **4.3** VideoDriver (subprocess `ffprobe`, degradation timeout wrapper)
- [x] **4.4** AudioDriver (Mutagen metadata)
- [x] **4.5** DocumentDriver (PyMuPDF `page_count` / `python-docx`)
- [x] **4.6** `AssetDriverManager` threading wrapper `asyncio.to_thread`
- [x] **Regression**: `asset.metadata['image'].get('width')` populates correctlyadata["height"]` populated

## Phase 15: DAM — Core Services
> Detail: `des_docs/design/dam/dam_roadmap.md` Phase 5
- [x] **5.1** `AssetService.ingest()` (SHA-256 dedup, AFS write, MIME detect, emit event)
- [x] **5.2** `AssetService.delete()` (AFS + thumbnails + links + albums + Qdrant point)
- [x] **5.3** `ThumbnailGenerator` (Pillow WebP, 3 sizes, EXIF rotation, GIF→first-frame)
- [x] **5.4** `DAMHooks.register_services` + EventBus wiring (`dam:asset:ingested`)
- [x] **5.5** `WatcherService` (watchdog, watch_paths from settings, `on_startup_async`)
- [x] **Regression**: Same file ingested twice → 1 Asset doc. Thumbnail at `{cache_dir}/{id}/200.webp`

## Phase 16: DAM — Vector Service
> Detail: `des_docs/design/dam/dam_roadmap.md` Phase 6
- [x] **6.1** `VectorDefinition` dataclass (`clip` 512-d Cosine)
- [x] **6.2** `VectorService.__init__` + `ensure_collection` (idempotent, graceful on Qdrant down)
- [x] **6.3** `VectorService.index()` + `delete()` (Qdrant upsert, ObjectId hex string Point ID)
- [x] **6.4** `VectorService.search()` (Qdrant ANN, `owner_id` keyword filter)
- [x] **6.5** `DAMHooks.register_vector_definitions` hookimpl
- [x] **Degradation**: Qdrant down → `_available=False`, app boots, all search channels return `[]`

## Phase 17: DAM — AI Processing Pipeline
> Detail: `des_docs/design/dam/dam_roadmap.md` Phase 7
- [x] **7.1** `BasePipelineProcessor` Protocol + `PipelineOrchestrator` (processor error isolation, `status="partial"`)
- [x] **7.2** CLIP embedding processor (`lru_cache` model load, `clip` 512-d vector)
- [x] **7.3** BLIP captioning processor (`ai_caption`, `transformers` base model)
- [x] **7.4** SmileWolf tagger processor (`TagProcessor`, WD14 ONNX)
- [x] **7.5** Object detection processor (`DetectionProcessor`, YOLOv8)
- [x] **7.6** Vector relation creator (`VectorRelationProcessor`, multi-vector fusion)
- [x] **7.7** TaskIQ task wrapping + EventBus subscription (`dam:asset:ingested` → enqueue `run_ai_pipeline`)
- [x] **Benchmark**: Optimized startup via local imports (collection time < 5s)

## Phase 18: DAM — Search & Discovery
> Detail: `des_docs/design/dam/dam_roadmap.md` Phase 8
- [x] **8.1** Search schema models (`AssetFilter.to_mongo_match()`, `SearchRequest`, `SearchPage`, cursor)
- [x] **8.2** Keyword search channel (MongoDB `$text`, `textScore`)
- [x] **8.3** Vector search channel (CLIP encode → Qdrant ANN, `_available` guard)
- [x] **8.4** Graph expansion channel (Knowledge Graph walk in `UnifiedSearchService`)
- [x] **8.5** RRF fusion (`k=60`) + cursor pagination + `search()` assembly
- [x] **8.6** `_compute_facets()` + `find_similar()` + pHash fallback + reverse image search
- [x] **Regression**: Full-text search, vector search, and graph walk each independently testable

## Phase 19: DAM — API Layer
- [x] **9.1** Asset CRUD endpoints (`POST`, `GET`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`)
- [x] **9.2** Thumbnail (`GET /{id}/thumbnail/{size}` WebP + Cache-Control) + download endpoints
- [x] **9.3** Search endpoints (`POST /search`, `GET /types`)
- [x] **9.4** Graph (`GET /{id}/links`) + Album CRUD (7 endpoints)
- [x] **9.5** Pipeline status (`GET /pipeline/status`)
- [x] **Regression**: All routes verified via integration tests in `tests/modules/dam/test_backend_gaps.py`.

## Phase 20: DAM — UI & Integration
> Detail: `des_docs/design/dam/dam_roadmap.md` Phase 10
- [x] **10.1** `DAMHooks.register_ui` full wiring (launchpad card, sidebar, ⌘K, all slot registrations)
- [x] **10.2** Gallery page `/dam` (grid, filter sidebar, infinite scroll, multi-select, empty state)
- [x] **10.3** Upload dropzone dialog (multi-file, per-file progress, auto-close on ready)
- [x] **10.4** Asset Viewer `/dam/assets/{id}` (preview + bbox SVG overlay + 3-tab panel + page slots)
- [x] **10.5** Search page `/dam/search`, Albums pages `/dam/albums`, Graph Explorer `/dam/graph`
- [x] **10.6** Shell components: `dam_quick_upload_button`, `dam_storage_widget`, `dam_asset_picker_overlay`
- [x] **10.7** Admin widget `DAMAdminWidget` (coverage bars, reprocess button)
- [x] **10.8** `DAMSettings` 20 fields, admin settings tab
- [x] **10.9** Blogger cross-module integration (PageSlot injection + cover image picker)
- [x] **Full degradation test**: Qdrant off / AI off / text index off — all pages remain functional

---

## DAM Knowledge Log
> Append learnings here during DAM implementation.

*   **2026-02-21**: DAM roadmap created.
    *   *Architecture*: 10 phases in `dam_roadmap.md` mirror dam_design.md §1–§10.
    *   *Infrastructure*: Qdrant `v1.9.2` added to `docker-compose.yml` (REST :6333, gRPC :6334).
    *   *Key decision*: Qdrant ID must be `uint64` — convert `ObjectId` via `abs(hash(str(id))) % (2**63)`.
    *   *Key decision*: `on_startup_async` must NOT use `firstresult=True`; all modules must run it.
    *   *Key decision*: `python-magic-bin` required on Windows (provides `libmagic`).
*   **2026-02-21**: Phase 11 (DAM Phase 1) Completed.
    *   *System*: Expanded `WebOSHookSpec` with 7 new DAM-specific endpoints (`register_services`, `on_startup_async`, etc.).
    *   *Lifespan*: Integrated `trigger_startup_async()` in FastAPI lifecycle for async initialization.
    *   *UI*: Refactored `UI_Slot` to permit arbitrary named slots with `kwargs` unpacking, enabling generic component injection across modules.
    *   *UI*: Created `PageSlotRegistry` for declarative DOM injection boundaries.
*   **2026-02-21**: Phase 12 (DAM Phase 2) Completed.
    *   *Design*: Initialized Beanie models (`Asset`, `Link`, `Album`) spanning search indexing requirements.
    *   *Bug*: Resolved Python C3 MRO inheritance conflict by avoiding extending `CoreDocument` whenever inheriting purely from `OwnedDocument` because it extends `CoreDocument` itself.
*   **2026-02-21**: Phase 13 (DAM Phase 3) Completed.
    *   *Design*: Migrated AssetType from Enums to an AssetTypeDefinition Interface dictating resolution capabilities (`can_handle(mime)`), hooked via `register_asset_types`.
    *   *Testing*: FastAPI TestClient requires hooking into `LifespanManager(app)` manually using HTTPX ASGITransport to evaluate async startup hooks reliably during module execution.
*   **2026-02-21**: Phase 11-14 Completed.
    *   *System*: Hook system, Beanie models, and sync Asset Drivers (Image, Video, etc.) implemented.
*   **2026-02-21**: Phase 15-17 Completed (Intelligence Core).
    *   *Vector*: Qdrant integration requires `uint64` or `UUID` Point IDs. Using `str(asset.id)` (hex) works as a UUID Point ID.
    *   *Conflict*: `qdrant-client` 1.17+ has `TypeError` with `protobuf` 5.x on Windows. Fixed by pinning `qdrant-client==1.12.0` and `protobuf==4.25.3`.
    *   *Performance*: Heavy AI libraries (`torch`, `transformers`) significantly slow down `pytest` collection. Moved imports inside class methods to keep the core loop fast.
    *   *Design*: Replaced string-based `patch` with `patch.object` in tests to avoid `AttributeError` when patching refactored local imports.
    *   *Wiring*: EventBus `dam:asset:ingested` now triggers both synchronous drivers (thumbnails/metadata) and asynchronous AI tasks (TaskIQ).
*   **2026-02-21**: Phase 18 (DAM Phase 8) Completed.
    *   *Search*: Implemented **Reciprocal Rank Fusion (RRF)** for hybrid search. Key learning: RRF constant `k=60` provides a robust balance between keyword precision and semantic recall.
    *   *Testing*: Debugged `mongomock_motor` limitations with `AsyncIOMotorLatentCommandCursor` during aggregation. For unit tests, complex aggregation pipelines on Beanie models may require mocking or raw collection access, while production remains standard Beanie.
*   **2026-02-21**: Phase 19 (DAM Phase 9) Completed.
    *   *AI*: Encountered `RuntimeError` and circularity issues with `torchvision` initialization on Windows. Refactored `StructuralProcessor` to use `transformers` with `google/mobilenet_v2_1.0_224` for better stability.
    *   *AI*: Integrated SmileWolf WD14 (ONNX) for tagging and YOLOv8 for object detection.
    *   *Graph*: Implemented `VectorRelationProcessor` for multi-vector cosine similarity fusion (CLIP + BLIP + MobileNet).
    *   *Search*: Added Graph Expansion channel to search, enabling discovery of "visually similar" and contextually related assets via the knowledge graph.
    *   *Beanie*: Standardized query syntax to use dictionary-based `$or` and `$in` filters. Bitwise operators (`|`) in Beanie DSL can trigger `TypeError` (ExpressionField not callable) in some mock/edge environments.
    *   *API*: Completed Album CRUD and Graph Link Explorer endpoints.
    *   *Validation*: Achieved 100% pass rate in `tests/modules/dam/test_backend_gaps.py`.
*   **2026-02-21**: Phase 20 (DAM Phase 10 UI & Integration) Completed.
    *   *UI*: Developed `ui/gallery.py` with faceted Search UI interfacing with `UnifiedSearchService`.
    *   *UI*: Built `ui/viewer.py` two-panel layout featuring previews and interactive tabs (INFO, AI, LINKS).
    *   *UI*: Implemented cross-module `DAMAdminWidget` in `ui/admin_widget.py` reporting real-time metrics.
    *   *Integration*: Registered global slots (Header Button, Dashboard Card) directly via `ui_slots.add()` leveraging NiceGUI routing context.
