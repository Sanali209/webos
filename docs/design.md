# Web OS Engine Design Document

## 1. Introduction

This document outlines the architectural design for the **Web OS Engine**, a robust platform built on **Clean Architecture** and **Ports & Adapters** (Hexagonal Architecture) principles. The goal is to provide a highly modular kernel that supports a diverse ecosystem of applications (modules).

### 1.1 Architecture Goals
- **Independence of Frameworks**: Business logic does not depend on FastAPI, NiceGUI, or Beanie.
- **Testability**: The core logic is testable without a database, UI, or web server.
- **Independence of UI**: The UI Kit is an interchangeable adapter.
- **Independence of Database**: The ODM (Beanie) is an implementation detail hidden behind repositories.

### 1.2 Key Principles
- **Ports & Adapters**: Define clear boundaries between Domain Logic (Kernel) and Infrastructure (UI, DB, External APIs).
- **Dependency Inversion**: High-level services depend on abstract interfaces (Ports), not concrete implementations (Adapters).
- **Plug-and-Play**: Modules are discovered and attached to the kernel via standardized hooks.

## 2. Architecture Overview

The system is structured into concentric layers, with the **Domain Kernel** at the center.

- **Kernel (Domain & Application)**: Contains pure business rules (Entities) and use case orchestration (Services).
- **Ports (Interfaces)**: Abstract definitions (ABCs) for data access, messaging, and storage.
- **Adapters (Infrastructure)**: Concrete implementations (Beanie Repositories, NiceGUI UI, TaskIQ Workers).

### 2.1 Core vs. Modules
- **Kernel/Core**: Provides the registry, DI container, and base abstractions.
- **Modules (Apps)**: Individual domains (e.g., Warehouse, CRM) that implement use cases and register their own adapters (UI, DB Collections).

## 3. Core SDK & Abstract Ports

The Engine provides a set of **Ports** (Abstract Base Classes) that ensure consistency and facilitate mocking during tests.

### 3.1 Base Service (`core.domain.BaseService`)
Standard foundation for orchestration logic. Services **never** interact with the DB directly; they use Repositories.

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional
from core.exceptions import DomainException

T = TypeVar("T")

class IRepository(ABC, Generic[T]):
    @abstractmethod
    async def get(self, id: str) -> Optional[T]: ...
    @abstractmethod
    async def save(self, entity: T) -> T: ...

class BaseService(Generic[T]):
    def __init__(self, repository: IRepository[T]):
        self.repo = repository

    async def fetch_item(self, id: str) -> T:
        item = await self.repo.get(id)
        if not item:
            raise DomainException(f"Resource {id} not found")
        return item
```

### 3.2 Access Control (`core.ports.SecurityPort`)
Secures the execution of use cases.
- **Port**: `ISecurityProvider` defines permission checks.
- **Adapter**: `FastAPIUsersAdapter` implements authentication logic.

### 3.3 Persistence & Storage
- **Repository Port**: Modules define their data access needs via Repositories.
- **Beanie Adapter**: Concrete classes inheriting from `CoreDocument` that handle MongoDB operations.

### 3.4 Messenger Port (`core.ports.UIOutputPort`)
- **Action**: `self.notify("Success")` is an abstract call.
- **Realization**: The NiceGUI adapter captures this and renders a toast.

### 3.5 Background Tasks
- **Engine**: TaskIQ (Infrastructure).
- **SDK**: `self.run_bg(task_instance)` abstracts the broker interaction.
### 3.6 Settings Service (`core.settings.SettingsService`)
A centralized "Control Panel" service for managing profiles, themes, and **System-wide configurations**.
- **User Settings**: Individual preferences (theme, notification toggles, profile info).
- **System Settings**: Global engine configurations (SMTP credentials, Storage backends, API keys for external services, Database maintenance).
- **Provider**: The Engine handles secure storage (MongoDB with encrypted fields for sensitive data) and provides a unified interface.
- **Schema-Driven**: Both modules and the core register settings schemas (Pydantic).

```python
class SettingsService:
    async def get_system_config(self, key: str) -> Any:
        """Fetch global system configuration."""
        ...

    async def update_system_config(self, key: str, value: Any):
        """Update a global setting with validation and permission check."""
        ...

    async def get_user_settings(self, user_id: str, module: str) -> dict:
        """Fetch settings for a specific user and module."""
        ...
```
```

## 4. Data Architecture (Entities vs. Persistence)

Following Clean Architecture, we separate the "What" (Domain Entity) from the "How" (Beanie/MongoDB Persistence).

### 4.1 Domain Entities (`core.domain.models`)
Pure Python objects representing business concepts. No dependence on Beanie.

```python
from pydantic import BaseModel
from datetime import datetime

class UserEntity(BaseModel):
    id: str
    email: str
    full_name: str
    permissions: List[str]
```

### 4.2 Beanie Adapters (`core.infrastructure.models`)
Concrete models that map Entities to MongoDB collections.

```python
from beanie import Document
from datetime import datetime

class UserDocument(Document, UserEntity):
    # Additional DB-specific fields (e.g., hashed_password)
    hashed_password: str
    
    class Settings:
        name = "users"
```

### 4.3 Repository Mapping
The Repository handles the conversion between `UserDocument` (Infrastructure) and `UserEntity` (Domain).

## 5. UI Architecture (NiceGUI Adapters)

The UI is treated as a **Delivery Mechanism** (Primary Adapter).

### 5.1 Component Pattern
Every UI unit is encapsulated in a class. Components never reach for the DB; they use **Domain Services**.

```python
class UserTableComponent:
    def __init__(self, user_service: UserService):
        self.service = user_service

    async def render(self):
        users = await self.service.list_active_users()
        # Render using NiceGUI
        ui.table(data=users)
```

### 5.2 Slot System (UI Extension Ports)
Modules register "Widget Factories" into predefined system slots.

- **Port**: `ISlotManager.register(slot_id, component_factory)`
- **Adapter**: Core shell iterates through factories to render the workspace.

### 5.3 System Pickers (Common UI Ports)
Standardized UI interactions provided as an SDK service.

```python
# Usage in a Domain Service (Application Layer) via Interface
class ProcessOrderService:
    def __init__(self, picker: IPickerPort):
        self.picker = picker

    async def run(self):
        # The service remains pure; the implementation of 'picker' 
        # is injected at runtime by the UI layer.
        file = await self.picker.select_file()
```

## 6. Module System & Lifecycle

Modules are Python packages in `src/modules/` that expose an entry point.

### 6.1 Module Interface
Updated protocol to include engine services registration.

```python
from typing import Protocol

class IModule(Protocol):
    name: str
    version: str
    settings_schema: type[BaseModel] # Pydantic schema for global settings
    
    def initialize(self, core_context):
        """Register routes, tasks, and data models."""
        ...
```

    
    def register_services(self, container: DIContainer):
        """Register repositories and services into the engine."""
        container.register(WarehouseRepo, BeanieWarehouseAdapter())
        container.register(WarehouseService, WarehouseService(WarehouseRepo))

    def mount_ui(self, slot_manager: ISlotManager):
        """Register UI components into the shell."""
        ...
```

## 7. Developer Experience (DX) & Business Logic SDK

### 7.1 Application Services (Use Cases)
The SDK provides `BaseApplicationService` to wrap common patterns like authorization checks and transaction management.

- **Command Pattern**: Services represent "Commands" (e.g., `PlaceOrderCommand`).
- **Input Validation**: Use `@validate_payload` to ensure data enters the domain cleanly.

### 7.2 Fluent Discoverability
To avoid manual wiring, the SDK uses a **Service Registry** that allows modules to "ask" for each other's public interfaces.

```python
# In Module A
warehouse = registry.get(IWarehouseService)
await warehouse.restock(item_id, quantity)
```

## 8. Inter-Module Communication (Events & Sagas)

When a process spans multiple modules, the Engine provides two patterns:

### 8.1 Async Events (Choreography)
Published via the **Event Bus**. Responders react to successful events (e.g., `OrderPaid` -> `Warehouse.reserve_items`).

### 8.2 Saga Coordinator (Orchestration)
For complex workflows requiring atomicity across modules, a **Saga** handles the sequence and compensating actions (rollbacks).

```python
class OrderSaga(BaseSaga):
    async def run(self, order_data):
        try:
            await self.payment.charge(order_data)
            await self.warehouse.reserve(order_data)
        except Exception:
            await self.payment.refund(order_data) # Compensating action
```

### 8.3 Command vs. Event
- **Command**: A request to perform an action (Single owner, can fail).
- **Event**: A notification that something happened (Multiple subscribers, statement of fact).

```python
# registry.py
class EventRegistry:
    _schemas = {}

    @classmethod
    def register(cls, event_name: str, schema: Type[BaseModel]):
        cls._schemas[event_name] = schema

    @classmethod
    def validate(cls, event_name: str, payload: dict):
        if event_name not in cls._schemas:
            raise ValueError(f"Unknown event: {event_name}")
        cls._schemas[event_name](**payload)  # Pydantic validation
```

## 8. Technology Stack

### 8.1 Core
- **Language**: Python 3.10+
- **Framework**: FastAPI (Web), Uvicorn/Gunicorn (Server)
- **Settings**: Pydantic Settings (Configuration management)

### 8.2 Database & Storage
- **Structure**: MongoDB
- **ODM**: Beanie (Async ODM for MongoDB)
- **Migrations**: `aerich` or custom script to handle schema evolution.
- **Caching**: DiskCache (Persistent caching)
- **File I/O**: Aiofiles (Async file operations)

### 8.3 Frontend / GUI
- **Framework**: NiceGUI (Vue/Quasar wrapper)
- **Styling**: Tailwind CSS
- **Assets**: Modules serve static files via `mount("/static/{module}", directory=...)`.
- **Client-Side Bridge**: Custom Vue components for high-interactivity widgets (Kanban, Drag-and-Drop) to avoid WebSocket latency.
- **Components**:
    - **AG Grid**: Advanced data tables.
    - **Plotly / Highcharts**: Data visualization.
    - **Lottie-python**: Animations.

### 8.4 Asynchronous Tasks
- **Engine**: TaskIQ
## 9. Technology Stack (Refined)

Selected for their ability to support Clean Architecture and high-performance async operations.

- **FastAPI / NiceGUI**: Primary Adapters for Web/UI.
- **Beanie (MongoDB)**: Secondary Adapter for persistence.
- **Dependency Injector**: Orchestrator for DI.
- **TaskIQ**: Infrastructure for distributed task execution.
- **Loguru**: Context-aware Logging.
- **Import-Linter**: Automated architectural boundary enforcement.
- **OpenTelemetry**: For observability across module boundaries.

## 10. Testing Strategy (Ports & Adapters)

The architecture enables a multi-layered testing approach.

### 10.1 Unit Testing (Domain Isolation)
- **Target**: Pure business logic (Kernel).
- **Strategy**: Inject "Test Adapters" (Mocks) into services to verify behavior without a DB or Network.

### 10.2 Integration Testing (Adapter Fidelity)
- **Target**: Concrete Adapters (Beanie Repositories, REST Clients).
- **Strategy**: Test against real (ephemeral) MongoDB instances or external service stubs.

### 10.3 Contract Testing
- **Target**: Port compliance.
- **Strategy**: Ensure that every Adapter implementation strictly follows the Port's ABC contract.

## 11. Critical Roadmap & Maturity

1.  **Domain Events (Stage 1)**: Moving from simple notifications to internal state-change events.
2.  **Boundary Guards (Stage 1)**: Implementing `import-linter` to prevent "Cross-Module Leaks."
3.  **Saga Persistence (Stage 2)**: Storing Saga state to handle multi-day or complex workflows.
4.  **Event Sourcing (Stage 3)**: Selective use of event sourcing for audit-heavy domains (e.g., Financials).
5.  **Observability (Stage 3)**: Distributed tracing to visualize the flow of events across the "Modulith."
