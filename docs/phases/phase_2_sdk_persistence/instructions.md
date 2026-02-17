# Phase 2: Core SDK & Persistence Ports - Instructions

## 🚀 Getting Started
Before starting this phase:
1. **Review [backlog.md](../../backlog.md)** for design decisions from Phase 1.
2. **Examine the `core.di` implementation** to understand how to register the new persistence ports.
3. **Analyze the current codebase** to ensure you are starting from a clean state.

## 🎯 Primary Goal
Enable modules to define their business logic and data models without being coupled to the database (MongoDB/Beanie).

## 📖 Related Documentation
- [Data Architecture](../design.md#4-data-architecture-entities-vs-persistence)
- [Technical Architecture (Mapping)](../architecture.md#3-data-flow-mapping-patterns)

## 🛠️ Tasks & Subtasks

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
    - [ ] Update SDK Developer Guide (Repositories & Services)
    - [ ] Create "Module Data Modeling" User Guide
- [ ] **Samples & Learning**:
    - [ ] Create `samples/02_task_manager`: Backend-only module using Repositories
    - [ ] Tutorial: "Building a headless business module"
    - [ ] **Testing**: Integration tests for task manager storage and retrieval

## ✅ Self-Check / Completion Criteria
- [ ] A Domain Service can fetch an "Entity" without importing anything from `beanie`.
- [ ] Contract tests confirm `BeanieAdapter` satisfies all `IRepository` methods.
- [ ] System settings are correctly cached in DiskCache and invalidated on update.
- [ ] `samples/02_task_manager` correctly persists data (confirmed by integration tests).
- [ ] Data modeling guide for module developers is complete.

## 📝 Post-Execution
Record the work in [backlog.md](../../backlog.md). Document the mapping logic used between Domain and Persistence layers and any performance considerations for the query DSL.
