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
- [ ] **Module Discovery Logic**
- [ ] **Auto-Wiring** (Routes/Models)
- [ ] **Pluggy Hooks**
- [ ] **CLI Tools**
- [ ] **Demonstration**: `src/modules/demo_hello_world/`
- [ ] **Regression**: Full suite + new module loader tests

## Phase 4: UI Engine (NiceGUI)
- [ ] **NiceGUI Integration**
- [ ] **Slot-Based Layout System**
- [ ] **Navigation & Menu**
- [ ] **Theme Engine**
- [ ] **Launchpad** (App Grid Component)
- [ ] **Demonstration**: `src/modules/demo_dashboard/`
- [ ] **Regression**: API Access + UI Playwright tests

## Phase 5: Storage & Caching
- [ ] **Storage Protocol & Local Backend**
- [ ] **Abstract File System (AFS)**
- [ ] **S3 Backend**
- [ ] **Caching Module** (DiskCache)
- [ ] **Demonstration**: `scripts/demo_storage.py`
- [ ] **Regression**: Verify I/O abstractions + previous tests

## Phase 6: Task System (TaskIQ)
- [ ] **TaskIQ Setup**
- [ ] **Context Propagation Middleware**
- [ ] **Task UI Widget**
- [ ] **Demonstration**: `src/modules/demo_report/`
- [ ] **Regression**: Verify Async Task execution + Core integrity

## Phase 7: Extensible Admin & Polish
- [ ] **Admin Dashboard Module**
- [ ] **Extensible Inspector**
- [ ] **Settings Editor**
- [ ] **Security & Perf Review**
- [ ] **Demonstration**: Complete System Demo (Admin Panel)
- [ ] **Regression**: Final Full Suite Run (Zero Failures)

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
