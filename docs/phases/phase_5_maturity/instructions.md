# Phase 5: Resilience & Maturity - Instructions

## 🚀 Getting Started
Before starting this phase:
1. **Review [backlog.md](../../backlog.md)** to understand the full architectural state.
2. **Analyze the inter-module dependency graph** to identify potential leak points.

## 🎯 Primary Goal
Harden the architecture with guards, observability, and automated documentation.

## 📖 Related Documentation
- [Architectural Guardrails](../architecture.md#5-architectural-guardrails)
- [Testing Strategy](../design.md#10-testing-strategy-ports--adapters)

## 🛠️ Tasks & Subtasks

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

## ✅ Self-Check / Completion Criteria
- [ ] Running the linter fails if a `domain` file imports from `infrastructure`.
- [ ] A single trace ID spans a UI action, a service call, and a background task.
- [ ] The engine boots successfully even if one module in `src.modules` is corrupted.
- [ ] SDK documentation is generated automatically via MkDocs.
- [ ] Capability maps for core modules are correctly generated and verified.

## 📝 Post-Execution
Record the work in [backlog.md](../../backlog.md). Document the final state of the engine's maturity and any recommendations for future module developers.
