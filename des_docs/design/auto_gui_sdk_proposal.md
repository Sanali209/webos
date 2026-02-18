# Proposal: Auto-GUI SDK for Pydantic & Beanie

This document outlines the design for an SDK module that automatically generates user interfaces for interacting with Pydantic models and Beanie database documents, fulfilling the "Auto Forms SDK" requirement.

## Propositions: 3 Approaches

### 1. The "AutoForm" Component (Recursive Mapper)
This approach focuses on generating a single form for a specific object instance or class.

*   **Logic**: A utility function `sdk.auto_form(model_class, target_object=None)` that inspects Pydantic field types.
*   **Mapping**:
    *   `str` -> `ui.input`
    *   `int`/`float` -> `ui.number`
    *   `bool` -> `ui.switch`
    *   `datetime` -> `ui.date` + `ui.time`
    *   `Enum` -> `ui.select`
    *   `Link[T]` -> `ui.select` (populated with search logic)
*   **Pros**: Highly granular, works for anything (even non-DB models), easy to embed in existing pages.
*   **Cons**: No built-in list management.

### 2. The "DataExplorer" (Editable AG Grid)
This approach focuses on bulk data management and exploration using AG Grid.

*   **Logic**: `sdk.data_grid(beanie_document_class)` generates a `ui.aggrid` pre-configured for the document's schema.
*   **Features**:
    *   `editable: True` on columns derived from model fields.
    *   Manual save button or auto-sync on `cellValueChanged`.
    *   Automatic column headers from Pydantic `Field(description=...)` or title-cased field names.
*   **Pros**: Excellent for power users, handles large datasets, feels "Pro".
*   **Cons**: Complex to implement validation in-grid; difficult to handle nested models.

### 3. The "AutoCrud" Framework (Full Controller)
A "Low-Code" approach that generates a complete management interface.

*   **Logic**: `sdk.register_crud(app_metadata, beanie_document_class)` registers a full app in the WebOS `ui_registry`.
*   **Layout**:
    *   **List View**: AG Grid for searching, filtering, and selecting.
    *   **Detail View**: An "AutoForm" in a side-drawer or modal for precise editing.
    *   **Hooks**: Provides hooks like `on_before_save`, `on_after_delete` for business logic overrides.
*   **Pros**: Massive developer productivity boost; consistent UI across all business modules.
*   **Cons**: Heaviest implementation; requires standardizing how data is fetched/filtered.

## Recommended Integration Points

1.  **`src/core/sdk/gui.py`**: New location for these helpers.
2.  **`OwnedDocument` Support**: The SDK should automatically detect if a model inherits from `OwnedDocument` and apply `owner_id` filtering.
3.  **AG Grid Integration**: We will need `ui.aggrid` (NiceGUI built-in wrapper for ag-grid-community).

## Next Steps

1.  Create a prototype of the **AutoForm** mapper.
2.  Implement a generic **CRUD Controller** that uses AG Grid for the list view.
3.  Add an example "Admin Explorer" module as a showcase.
