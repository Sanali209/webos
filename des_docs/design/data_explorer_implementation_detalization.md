# Implementation Plan: DataExplorer SDK (Approach 2)

This plan details the implementation of an AG Grid-based "DataExplorer" that automatically maps Beanie documents to an editable grid interface.

## Technical Architecture

The SDK will reside in `src/core/sdk/data_explorer.py` and provide a high-level component `DataExplorer`.

### 1. Schema-to-Column Mapping
The SDK will inspect the Beanie `Document` (Pydantic model) to generate `columnDefs`:
*   **Field Mapping**:
    *   `str` -> `editable: True`
    *   `bool` -> `cellRenderer: 'agCheckboxCellRenderer'`, `editable: True`
    *   `int`/`float` -> `valueParser: 'Number(params.newValue)'`, `editable: True`
    *   `datetime` -> `cellEditor: 'agDateCellEditor'`
*   **Metadata**: Use `pydantic.Field` descriptions for column titles. Hide internal fields like `_id`, `revision_id`, `owner_id` by default.

### 2. Data Lifecycle & Isolation
*   **Fetch**: Uses `Document.find()`. If the document inherits from `OwnedDocument`, it automatically applies `owner_id == current_user_id`.
*   **Update**: Listens to `cellValueChanged` event. 
    *   The SDK will fetch the document by `id`.
    *   Update the specific field using `set({field: new_value})`.
    *   Handle validation errors via `ui.notify`.
*   **Create/Delete**: Integrated buttons at the top of the grid to trigger modals/confirmation.

### 3. Usage Patterns

#### A. Database-Backed (Beanie)
Automatically handles CRUD with MongoDB.
```python
DataExplorer(model=Secret) # Fetches and saves to DB
```

#### B. In-Memory (Pure Pydantic)
Edit a list of Pydantic objects. The grid will emit an `on_change` event with the updated list or specific object.
```python
class MyConfig(BaseModel):
    key: str
    value: int

items = [MyConfig(key="A", value=1), MyConfig(key="B", value=2)]

def handle_update(updated_items):
    print(f"New state: {updated_items}")

DataExplorer(
    model=MyConfig, 
    items=items, 
    on_change=handle_update
)
```

## Proposed Changes

### [Component] Core SDK

#### [NEW] [data_explorer.py](file:///d:/github/webos/src/core/sdk/data_explorer.py)
*   Implement `DataExplorer` class wrapping `ui.aggrid`.
*   Add logic for `_generate_column_defs(model_class)`.
*   Add logic for `_handle_cell_change(event)`.
*   Integrate with `user_id_context` for `OwnedDocument` filtering.

### [Component] Modules (Example Usage)

#### [MODIFY] [ui.py](file:///d:/github/webos/src/modules/vault/ui.py) (Optional Prototype)
*   Replace manual table with `DataExplorer(Secret)`.

## Verification Plan

### Automated Tests
*   **Unit Tests**: Verify `_generate_column_defs` correctly identifies types.
*   **Integration Tests**: Mock Beanie and verify `_handle_cell_change` triggers correct DB calls.

### Manual Verification
*   Open the Vault page.
*   Verify that columns match the `Secret` model.
*   Check that editing a cell (e.g., Label) saves to the DB immediately.
*   Verify that different users only see their own secrets (OwnedDocument isolation).
