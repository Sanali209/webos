# UI Framework Reference

WebOS uses NiceGUI to construct Python-based reactive user interfaces.

## Application Registration (`ui_registry`)

The `ui_registry` manages the top-level applications available in the main layout wrapper (like the sidebar).

```python
from src.ui.registry import ui_registry

def register_my_app():
    ui_registry.register_app(
        name="Settings",
        icon="settings",
        route="/settings",
        # Optional: Require specific permissions to view this app
        permission="admin.read" 
    )
```

## Page Slot Registry (`page_slot_registry`)

The `PageSlotRegistry` allows deep UI extensibility by letting modules inject UI elements directly into other modules' pages.

### Declare a Slot

```python
from src.ui.page_slot_registry import page_slot_registry
from nicegui import ui

def render_dashboard():
    ui.label("Dashboard")
    
    # Render all injected widgets dynamically
    page_slot_registry.render(path="dashboard", slot_name="widgets")
```

### Inject into a Slot

```python
from src.ui.page_slot_registry import page_slot_registry
from nicegui import ui

def build_my_widget():
    ui.button("Custom Action")

# Inject during application startup
page_slot_registry.inject(path="dashboard", slot_name="widgets", builder=build_my_widget)
```

## Theme Utilities (`theme.py`)

Standard CSS classes are available. It encapsulates the main structural logic so styling remains uniform across modules.

```python
from src.ui.theme import apply_theme

def page_builder():
    apply_theme()
```

## Auto-GUI SDK (`DataExplorer`)

The `DataExplorer` is a high-level UI component (`src.core.sdk.data_explorer.py`) that automatically generates a full-featured, editable data grid from any Pydantic or Beanie model. It wraps the powerful AG Grid library.

```python
from src.core.sdk.data_explorer import DataExplorer
from src.modules.inventory.models import Product

def render_inventory_grid():
    # Automatically creates columns, search, pagination, and editing 
    # based on the Product Beanie Document schema.
    explorer = DataExplorer(model=Product)
```
