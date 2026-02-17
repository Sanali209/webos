# Web OS Engine Implementation Roadmap

This roadmap outlines the implementation of the Web OS Engine in non-blocking phases, allowing for incremental development and early testing of the kernel.

## Phase 1: Foundation (The Micro-Kernel)
**Goal**: Establish the dependency injection container and module loading system.

### 1.1 Implement `core.di.Container`
- [ ] Develop the registry and resolution engine
    - [ ] Create `DIContainer` with thread-safe registration
    - [ ] Support type-hint based resolution
    - [ ] Implement Lifetime Management (Singleton, Scoped, Transient)
- [ ] Create Constructor Injection Logic
    - [ ] Build a recursive resolver for nested dependencies
    - [ ] Implement `@inject` decorator for classes and functions
- [ ] **Testing**:
    - [ ] Unit tests for circular dependency detection
    - [ ] Performance benchmarks for resolution depth

### 1.2 Set up `pluggy` hooks
- [ ] Define Core Hook Specifications
    - [ ] `post_setup`: Called after kernel init
    - [ ] `on_module_load`: Triggered when a module is discovered
    - [ ] `mount_ui`: Registration for UI components
- [ ] Implement Module Discovery Engine
    - [ ] Use namespace package scanning for `src.modules.*`
    - [ ] Implement dynamic import error handling and logging
- [ ] **Testing**:
    - [ ] Integration tests for module discovery with dummy plugins

### 1.3 Implement `IModule` protocol and boot sequence
- [ ] Formalize Module Interface
    - [ ] Define required attributes (`name`, `version`)
    - [ ] Define lifecycle methods (`initialize`, `shutdown`)
- [ ] Orchestrate Engine Boot
    - [ ] Create `Engine.start()` with phase ordering
    - [ ] Implement dependency graph sorting for module initialization
- [ ] **Testing**:
    - [ ] Boot sequence logging and timing verification
- [ ] **Documentation**:
    - [ ] [NEW] Generate Core Kernel Developer Guide (DI & Hooks)
    - [ ] [NEW] Create Engine Bootstrapping User Manual
- [ ] **Samples & Learning**:
    - [ ] [NEW] Create `samples/01_hello_kernel`: Minimal bootable engine with one hook
    - [ ] [NEW] Tutorial: "My First Kernel Hook" implementation guide
    - [ ] [NEW] **Testing**: Automated smoke test for `hello_kernel` boot success

### 1.4 Create base `DomainException` and boundaries
- [ ] Exception Hierarchy
    - [ ] `BaseEngineException` -> `KernelError`, `ModuleError`
    - [ ] `AccessDeniedError` for security violations
- [ ] Error Isolation
    - [ ] Implement "Try/Except" wrappers for all plugin hook calls
    - [ ] Create a "Faulty Module" registry for recovery
- [ ] **Testing**:
    - [ ] Chaos tests: verifying kernel stability when modules crash during init

## Phase 2: Core SDK & Persistence Ports
**Goal**: Enable modules to define their data models and business logic without DB coupling.

### 2.1 Define `IRepository` abstract base classes
- [ ] Create Generic Port Interfaces
    - [ ] `IReadRepository[T]` with search and fetch methods
    - [ ] `IWriteRepository[T]` with commit and rollback methods
- [ ] Standardize Query Objects
    - [ ] Implement a backend-agnostic `FilterCriteria` DSL
- [ ] **Testing**:
    - [ ] Unit tests for `FilterCriteria` serialization

### 2.2 Implement `BaseService` orchestration foundation
- [ ] Create Application Service SDK
    - [ ] Automated logging of all service calls
    - [ ] Contextual metadata handling (Tenant, User, RequestID)
- [ ] Implement Transactional Boundaries
    - [ ] Context manager for unit-of-work across multiple repositories
- [ ] **Testing**:
    - [ ] Mock-based unit tests for service orchestrations

### 2.3 Build `BeanieAdapter` for MongoDB
- [ ] Persistence Implementation
    - [ ] Map `CoreDocument` to Beanie `Document`
    - [ ] Implement the `IRepository` logic for MongoDB/Beanie
- [ ] Database Discovery
    - [ ] Automated collection registration for all loaded modules
- [ ] **Testing**:
    - [ ] Integration tests with `mongomock` or ephemeral Testcontainers
    - [ ] Contract tests verifying BeanieAdapter satisfies `IRepository`

### 2.4 Implement `SettingsService`
- [ ] Global Configuration Engine
    - [ ] MongoDB-backed key-value store for system settings
    - [ ] In-memory caching layer with invalidation (DiskCache)
- [ ] User Preference API
    - [ ] Scoped settings by `user_id` and `module_id`
- [ ] **Testing**:
    - [ ] Cache hit/miss and invalidation integration tests
- [ ] **Documentation**:
    - [ ] [NEW] Update SDK Developer Guide (Repositories & Services)
    - [ ] [NEW] Create "Module Data Modeling" User Guide
- [ ] **Samples & Learning**:
    - [ ] [NEW] Create `samples/02_task_manager`: Backend-only module using Repositories
    - [ ] [NEW] Tutorial: "Building a headless business module"
    - [ ] [NEW] **Testing**: Integration tests for task manager storage and retrieval

## Phase 3: UI Adapter & Shell
**Goal**: Provide a delivery mechanism for modules using NiceGUI.

### 3.1 Implement `SlotManager` for UI extension points
- [ ] Shell Slot Registry
    - [ ] Define standard slots (`navbar`, `sidebar`, `main`, `widgets`)
    - [ ] Implementation of weighted registration (order of widgets)
- [ ] Dynamic Content Rendering
    - [ ] Async rendering of widgets from multiple modules into a single slot
- [ ] **Testing**:
    - [ ] UI Component registration and priority tests

### 3.2 Build `Component` base class
- [ ] UI Unit Encapsulation
    - [ ] Support for reactive state within components
    - [ ] Automated CSS class scoping and Tailwind utility injection
- [ ] Component Lifecycle
    - [ ] `on_mount` and `on_unmount` hooks for NiceGUI elements
- [ ] **Testing**:
    - [ ] Lifecycle hook execution verification

### 3.3 Implement `IPickerPort` and NiceGUI Adapters
- [ ] Common Selectors SDK
    - [ ] `FilePicker`: Local NAS/Minio file selection modal
    - [ ] `UserPicker`: Searchable multi-select for engine users
- [ ] Adapter Realization
    - [ ] Full NiceGUI/Quasar implementation of modal-based pickers
- [ ] **Testing**:
    - [ ] Visual regression tests for standardized pickers

### 3.4 Create main OS Shell
- [ ] Workspace Layout
    - [ ] Fluid sidebar with module navigation icons
    - [ ] Top bar with search, notifications, and user profile
- [ ] Breadcrumb and Navigation Service
    - [ ] Global route management and active module state tracking
- [ ] **Testing**:
    - [ ] E2E navigation flows with Playwright
- [ ] **Documentation**:
    - [ ] [NEW] Update UI Developer Guide (Components & Slots)
    - [ ] [NEW] Create "Building Your First Module UI" User Manual
- [ ] **Samples & Learning**:
    - [ ] [NEW] Create `samples/03_dashboard_widget`: Interactive UI component in the OS shell
    - [ ] [NEW] Tutorial: "Extending the OS interface with your module"
    - [ ] [NEW] **Testing**: UI interaction tests for the dashboard widget sample

## Phase 4: Advanced Orchestration
**Goal**: Handle complex, multi-module business processes.

### 4.1 Implement `EventBus` with schema validation
- [ ] Distributed Event Hub
    - [ ] Support for both `fire-and-forget` and `wait-for-result` events
    - [ ] Pydantic-based schema validation for all event payloads
- [ ] Schema Registry
    - [ ] Service to query available event types and their structures
- [ ] **Testing**:
    - [ ] Payload validation tests (Success/Fail cases)

### 4.2 Build `SagaCoordinator`
- [ ] Distributed Transaction Manager
    - [ ] State persistence for long-running sagas
    - [ ] Definition of "Compensating Actions" (Rollback functions)
- [ ] Saga DSL
    - [ ] Fluent interface for defining multi-step sequences
- [ ] **Testing**:
    - [ ] Rollback/Compensation verification tests (Simulated Failures)

### 4.3 Differentiate `Command` vs `Event` flows
- [ ] SDK Semantics
    - [ ] `bus.send(Command)` for single-target actions
    - [ ] `bus.publish(Event)` for multi-subscriber notifications
- [ ] Middleware Support
    - [ ] Command pre-processing (Auth, Validation)
    - [ ] Event tracing (Auditing)
- [ ] **Testing**:
    - [ ] Middleware execution order and auth-guard tests

### 4.4 Integrate `TaskIQ` for persistence
- [ ] Background Worker SDK
    - [ ] Wrapper for `@broker.task` that auto-injects module context
    - [ ] UI for task progress, logs, and manual retry
- [ ] **Testing**:
    - [ ] End-to-end background job execution and UI monitoring
- [ ] **Documentation**:
    - [ ] [NEW] Update Orchestration Developer Guide (Events & Sagas)
    - [ ] [NEW] Create "Inter-Module Communication" User Manual
- [ ] **Samples & Learning**:
    - [ ] [NEW] Create `samples/04_order_saga`: Multi-module workflow example
    - [ ] [NEW] Tutorial: "Coordinating complex processes with Sagas"
    - [ ] [NEW] **Testing**: Verifying the full saga workflow and compensation in the sample

## Phase 5: Resilience & Maturity
**Goal**: Protect the architecture and enhance developer experience.

### 5.1 Integrate `import-linter`
- [ ] Boundary Enforcement
    - [ ] Define `layers.yaml` for `domain` -> `application` -> `infrastructure`
    - [ ] CI/CD blocker for cyclic or layer-violating imports
- [ ] **Testing**:
    - [ ] Automated linting in CI/CD pipeline

### 5.2 Implement `OpenTelemetry` tracing
- [ ] Full-Stack Observability
    - [ ] Tracing events from UI action -> Service -> DB -> TaskIQ
    - [ ] Visual dashboard for inter-module call graphs
- [ ] **Testing**:
    - [ ] Trace propagation verification across async boundaries

### 5.3 Build "Safe Mode" boot sequence
- [ ] Fault-Tolerant Loading
    - [ ] Mechanism to skip modules that raise `ModuleLoadError`
    - [ ] Engine-level toast notification for module initialization failures
- [ ] **Testing**:
    - [ ] Resilience tests: booting with partially corrupted module registry

### 5.4 Finalize `AutoForms SDK`
- [ ] Model-to-UI Engine
    - [ ] Introspection of Pydantic fields to generate inputs (Select, Date, Text)
    - [ ] Automated "Save" button wiring to appropriate domain services
- [ ] **Testing**:
    - [ ] Dynamic form validation and submission tests

### 5.5 Automated Document Generation
- [ ] SDK & API Documentation
    - [ ] Implementation of `MkDocs` with `mkdocstrings` for automated Python API docs
    - [ ] Automated UML class diagram generation from Domain Entities
- [ ] Module Blueprint Generator
    - [ ] Tool to generate a "Capability Map" (which events/commands a module exposes)
- [ ] Schema-to-Docs Pipeline
    - [ ] Exporting Pydantic models to Markdown/HTML for module developers
- [ ] **Testing**:
    - [ ] Docstring coverage auditing in CI/CD
