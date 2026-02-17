# Phase 3: UI Adapter & Shell - Instructions

## 🚀 Getting Started
Before starting this phase:
1. **Review [backlog.md](../../backlog.md)** for updates on the SDK capabilities.
2. **Check the `core.domain` models** to ensure the UI components align with the domain entities.
3. **Analyze the current state of the DI container** to understand how to mount UI extension points.

## 🎯 Primary Goal
Implement the NiceGUI-based delivery mechanism and the primary OS shell.

## 📖 Related Documentation
- [UI Architecture](../design.md#5-ui-architecture-nicegui-adapters)
- [System Pickers Port](../design.md#53-system-pickers-common-ui-ports)

## 🛠️ Tasks & Subtasks

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
    - [ ] Update UI Developer Guide (Components & Slots)
    - [ ] Create "Building Your First Module UI" User Manual
- [ ] **Samples & Learning**:
    - [ ] Create `samples/03_dashboard_widget`: Interactive UI component in the OS shell
    - [ ] Tutorial: "Extending the OS interface with your module"
    - [ ] **Testing**: UI interaction tests for the dashboard widget sample

## ✅ Self-Check / Completion Criteria
- [ ] A module can inject a widget into the `dashboard_slot` via the DI container.
- [ ] Playwright tests confirm navigation between two dummy modules works.
- [ ] `samples/03_dashboard_widget` is correctly rendered and reactive.
- [ ] UI Developer Guide correctly describes the component lifecycle.
- [ ] Pickers return correct values to domain services without breaking isolation.

## 📝 Post-Execution
Record the work in [backlog.md](../../backlog.md). List the available UI slots and any "gotchas" regarding NiceGUI async rendering.
