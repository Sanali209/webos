# Proposal: Persistent Module Settings System

This document outlines the architecture for a decentralized, persistent settings system for WebOS modules, integrated with the DataExplorer SDK and Admin Panel.

## Architectural Design

### 1. The `register_settings` Hook
We will extend the `WebOSHookSpec` to allow modules to define their own configuration schemas using Pydantic.

```python
# src/core/hooks.py
@hookspec
def register_settings() -> Type[BaseModel]:
    """Return a Pydantic model class representing the module's settings."""
```

### 2. Persistence Layer (Beanie)
A centralized document will store the serialized settings for all modules.

```python
# src/core/models/settings.py
class ModuleSettingsDoc(CoreDocument):
    module_name: str = Indexed(unique=True)
    values: Dict[str, Any] = {}

    class Settings:
        name = "system_settings"
```

### 3. Settings Management Service
A core service will bridge the gap between Pydantic schemas and MongoDB.

*   **Registry**: Stores the mapping of `module_name -> PydanticClass`.
*   **Loading**: On system startup (after DB init), the service fetches `ModuleSettingsDoc` and instantiates the Pydantic models with the stored values.
*   **Access**: Modules can access their settings via `settings_service.get(module_name)`.

### 4. Admin Integration (DataExplorer)
The Admin panel will provide a "Module Settings" view. For each module:
1.  The UI fetches the Pydantic schema class.
2.  It converts the current settings object into a "Key-Value" list for the `DataExplorer`.
3.  **DataExplorer** renders an editable grid where:
    *   Column 1: Setting Key (Read-only)
    *   Column 2: Current Value (Editable)
    *   Column 3: Description (From Pydantic `Field(description=...)`)

### 5. Integration Points & Solidity
*   **Pluggy**: Perfectly suited for collecting schemas.
*   **Beanie**: Provides robust persistence.
*   **NiceGUI + AG Grid (DataExplorer)**: Provides a professional, responsive editing experience.
*   **Context Propagation**: Settings updates should emit an event on the Event Bus so modules can react to configuration changes in real-time without restarts.

## Implementation Plan

1.  **Core Updates**:
    *   Modify `src/core/hooks.py` to add `register_settings`.
    *   Create `src/core/models/settings.py`.
    *   Create `src/core/services/settings_service.py`.
2.  **Loader Updates**:
    *   Update `src/core/module_loader.py` to collect settings during discovery.
3.  **SDK Updates**:
    *   Ensure `DataExplorer` supports a "Key-Value" mode or can easily handle a single-object proxy.
4.  **Admin Updates**:
    *   Create `src/modules/admin/settings_explorer.py` to host the new UI.

## Next Steps
1.  Implement the `register_settings` hook and `ModuleSettingsDoc`.
2.  Prototype the `SettingsService`.
3.  Update the Admin UI to use `DataExplorer` for these settings.
