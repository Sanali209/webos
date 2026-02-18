# UI & Layout System

The WebOS UI is powered by **NiceGUI** and follows a hybrid "Slot-based" architecture. This allows modules to inject components into the global shell (Sidebar, Header, Dashboard) without modifying a single line of core code.

## 1. The Shell: `MainLayout`

The `MainLayout` (in `src.ui.layout`) is the root container for all WebOS pages. It provides:
- A responsive **Header** (Logo, Search, Auth).
- A collapsible **Sidebar** (Navigation).
- A centralized **Content Area** for module-specific pages.
- A **Command Palette** (Ctrl+K).

### Usage in Modules
To use the shell in your module, wrap your page content in the `MainLayout` context manager:

```python
@ui.page("/my-page")
def my_page():
    with MainLayout():
        ui.label("I am now inside the WebOS Shell!")
```

## 2. Dynamic Slots

The `UI_Slot` system allows modules to register builder functions that are executed when specific layout areas are rendered.

### Available Slots
- `sidebar`: Appended to the bottom of the navigation drawer.
- `header`: Injected into the right side of the header bar.
- `dashboard_widgets`: Rendered as cards on the main dashboard landing page.
- `app_grid`: Injected into the Launchpad grid.

### Registering a Widget
In your module's `ui.py` or a registration hook:

```python
from src.ui.layout import ui_slots

def my_widget():
    with ui.card().classes("w-64"):
        ui.label("Live Sales: $4,500").classes("text-xl font-bold")

ui_slots.add("dashboard_widgets", my_widget)
```

## 3. The App Registry: `AppMetadata`

Every module that provides a primary entry point should register itself with the `ui_registry`. This metadata is what populates the **Launchpad** and the **Sidebar Navigator**.

```python
from src.ui.registry import ui_registry, AppMetadata

ui_registry.register_app(AppMetadata(
    name="Inventory",
    icon="inventory_2",
    route="/inventory",
    description="Manage warehouse stock."
))
```

## 4. Theming

WebOS uses a customized Tailwind configuration via NiceGUI. The global `theme` object (in `src.ui.theme`) handles:
- Color palettes (Primary, Secondary, Success, etc.).
- Dark mode persistence.
- Typography defaults.

---

## Next Steps
- Follow the [How-To: Add UI Elements](./add_ui_element.md).
- Learn how to [Manage Files](./file_ops.md).
- Explore the [Module System](./module_system.md).
