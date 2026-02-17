# Phase 2: Data Layer & Authentication Implementation Plan

This phase focuses on setting up the persistence layer using Beanie (ODM) and integrating FastAPI Users for authentication and authorization.

## Proposed Changes

### Core Data Layer
Implement the base document and mixins to be used across all modules.

#### [NEW] [models.py](file:///d:/github/webos/src/core/models.py)
*   Define `CoreDocument` inheriting from Beanie's `Document`.
*   Implement `AuditMixin` with `created_at`, `updated_at`, `created_by`, `updated_by`.
*   Implement `OwnedDocument` mixin for automated user isolation.

#### [NEW] [database.py](file:///d:/github/webos/src/core/database.py)
*   Implement `init_db` function to initialize Motor and Beanie.
*   Manage model discovery (standard core models + module models).

### Authentication & Security
Integrate FastAPI Users with Beanie backend.

#### [NEW] [auth.py](file:///d:/github/webos/src/core/auth.py)
*   Setup FastAPI Users with JWT strategy.
*   Define `User` document.
*   Implement `current_active_user` dependency.
*   Implement `@require_permission` decorator logic.

### Lifecycle Management
#### [MODIFY] [main.py](file:///d:/github/webos/src/main.py)
*   Create the main FastAPI application.
*   Add lifespan events to initialize DB and Logging.
*   Include auth routers.

## Verification Plan

### Automated Tests
*   **Database Init**: Verify connection to Mongo.
    *   `python -m pytest tests/core/test_database.py`
*   **Model Mixins**: Verify `AuditMixin` sets timestamps.
    *   `python -m pytest tests/core/test_models.py`
*   **User Isolation**: Verify `OwnedDocument` filters by user.
    *   `python -m pytest tests/core/test_isolation.py`
*   **Auth Flow**: Verify login and protected route access.
    *   `python -m pytest tests/core/test_auth.py`

### Demonstration
*   **`scripts/demo_auth_flow.py`**: A CLI script to register a user, login, and access a protected resource.
    *   Run: `.venv/Scripts/python scripts/demo_auth_flow.py`
