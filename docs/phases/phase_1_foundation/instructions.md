# Phase 1: Foundation (Micro-Kernel) - Instructions

## 🚀 Getting Started
Before starting this phase:
1. **Review [backlog.md](../../backlog.md)** to understand project context.
2. **Analyze the current codebase** to ensure you are starting from a clean state.

## 📖 Related Documentation
- [Architecture Deep Dive](../architecture.md#2-dependency-injection-di-container)
- [Design Principles](../design.md#1-introduction)
- [Clean Architecture Concepts](../design.md#2-architecture-overview)

## 🛠️ Tasks & Subtasks

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
    - [ ] Generate Core Kernel Developer Guide (DI & Hooks)
    - [ ] Create Engine Bootstrapping User Manual
- [ ] **Samples & Learning**:
    - [ ] Create `samples/01_hello_kernel`: Minimal bootable engine with one hook
    - [ ] Tutorial: "My First Kernel Hook" implementation guide
    - [ ] **Testing**: Automated smoke test for `hello_kernel` boot success

### 1.4 Create base `DomainException` and boundaries
- [ ] Exception Hierarchy
    - [ ] `BaseEngineException` -> `KernelError`, `ModuleError`
    - [ ] `AccessDeniedError` for security violations
- [ ] Error Isolation
    - [ ] Implement "Try/Except" wrappers for all plugin hook calls
    - [ ] Create a "Faulty Module" registry for recovery
- [ ] **Testing**:
    - [ ] Chaos tests: verifying kernel stability when modules crash during init

## ✅ Self-Check / Completion Criteria
- [ ] `DIContainer` correctly resolves a service with two nested dependencies.
- [ ] A module with a syntax error in `src.modules` does not crash the entire boot sequence (handled by boundaries).
- [ ] Unit tests for circular dependency detection pass.
- [ ] Developer guide for DI and Hooks is generated and accurate.
- [ ] `samples/01_hello_kernel` boots successfully (confirmed by smoke test).
- [ ] Faulty modules are correctly identified and isolated during boot.

## 📝 Post-Execution
Record the work in [backlog.md](../backlog.md). Detail the specific DI implementation choice and any discovered boot order complexities.
