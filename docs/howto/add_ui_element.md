# How-To: Add UI Elements

This guide shows you how to add new visual pages to your module and register them so they appear on the WebOS Launchpad.

## 1. Creating a Page

To create a new page, use the `@ui.page` decorator from NiceGUI. You should always wrap your content in the `MainLayout` context manager to maintain the system theme and navigation.

### Example
In `src/modules/your_module/ui.py`:

```python
from nicegui import ui
from src.ui.layout import MainLayout

@ui.page("/my-module-view")
def my_custom_page():
    with MainLayout():
        ui.label("My New View").classes("text-2xl font-bold")
        ui.button("Click Me!", on_click=lambda: ui.notify("Success!"))
```

## 2. Registering for the Launchpad

To make your app discoverable, you must register its metadata. The best practice is to do this inside a `register_ui` function decorated with `@hookimpl`.

### Example
```python
from src.ui.registry import ui_registry, AppMetadata
from src.core.hooks import hookimpl

@hookimpl
def register_ui():
    """Add my app to the system launchpad and sidebar."""
    ui_registry.register_app(AppMetadata(
        name="Inventory",
        icon="inventory",        # Google Material Icon name
        route="/my-module-view", # Must match the @ui.page route
        description="Monitor warehouse stock levels.",
        category="Business"      # Optional: Groups apps on the launchpad
    ))
```

## 3. Injecting into Slots

If you want to add a widget to an existing page (like the Dashboard) rather than creating a whole new page, use the `ui_slots` registry.

### Example: Dashboard Widget
```python
from src.ui.layout import ui_slots

def quick_stats_widget():
    with ui.card().classes("p-4 bg-blue-50"):
        ui.label("Daily Revenue").classes("text-sm text-slate-500")
        ui.label("$1,240").classes("text-2xl font-black")

# Register the builder function to the 'dashboard_widgets' slot
ui_slots.add("dashboard_widgets", quick_stats_widget)
```

## 4. Icons Reference

WebOS uses **Google Material Icons**. You can find a complete list of available icon names at [fonts.google.com/icons](https://fonts.google.com/icons). Simply use the name (e.g., `settings`, `person`, `mail`) in your `AppMetadata`.

---

## Next Steps
- Learn how to [Manage Files](./file_ops.md).
- Understand the [Authentication System](../concepts/auth_system.md).
- Explore the [Core Concepts](../tutorials/core_concepts.md).
