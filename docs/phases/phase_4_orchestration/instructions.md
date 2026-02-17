# Phase 4: Advanced Orchestration - Instructions

## 🚀 Getting Started
Before starting this phase:
1. **Review [backlog.md](../../backlog.md)** to understand the current engine state and previous design decisions.
2. **Analyze the source code** of `core.di` and `core.domain` to ensure you are building upon a stable foundation.

## 🎯 Primary Goal
Implement the Event Bus and Saga Coordinator for complex, inter-module orchestration.

## 📖 Related Documentation
- [Inter-Module Orchestration](../architecture.md#4-inter-module-orchestration)
- [Event Bus Design](../design.md#8-inter-module-communication-events--sagas)

## 🛠️ Tasks & Subtasks

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
    - [ ] Update Orchestration Developer Guide (Events & Sagas)
    - [ ] Create "Inter-Module Communication" User Manual
- [ ] **Samples & Learning**:
    - [ ] Create `samples/04_order_saga`: Multi-module workflow example
    - [ ] Tutorial: "Coordinating complex processes with Sagas"
    - [ ] **Testing**: Verifying the full saga workflow and compensation in the sample

## ✅ Self-Check / Completion Criteria
- [ ] An event emitted by Module A is validated and correctly received by Module B.
- [ ] A multi-step Saga correctly rolls back (compensation) if a step fails.
- [ ] Background tasks in TaskIQ are visible in the engine monitor.
- [ ] Orchestration Developer Guide covers both Event Bus and Saga patterns.
- [ ] `samples/04_order_saga` passes all workflow verification tests.

## 📝 Post-Execution
Record the work in [backlog.md](../../backlog.md). Document the Saga persistence strategy and any specific Event Bus middleware patterns implemented.
