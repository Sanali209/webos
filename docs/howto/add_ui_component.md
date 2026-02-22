# How-To: Add a UI Component

WebOS's frontend is powered by [NiceGUI](https://nicegui.io/). To allow modules to contribute UI elements to the main application without hardcoding them into the base layout, we use the `PageSlotRegistry`.

This guide explains how to declare a slot (if you are building a host page) and how to inject a component into a slot (if you are building a plugin module).

## 1. Injecting a Component (For Plugins)

If you want your module to add a widget to an existing page (for example, the `admin_dashboard`), you use the `page_slot_registry.inject` method.

We do this inside the `register_page_slots` hook to ensure it runs during application startup.

```python
# src/modules/my_plugin/__init__.py
from nicegui import ui
from src.core.hooks import hookimpl
from src.ui.page_slot_registry import page_slot_registry

def render_my_dashboard_widget():
    with ui.card().classes('w-full'):
        ui.label('Plugin Status').classes('text-lg font-bold')
        ui.label('System is operating normally.')

@hookimpl
def register_page_slots():
    # Inject our widget into the 'admin_dashboard' slot named 'widgets'
    page_slot_registry.inject('admin_dashboard', 'widgets', render_my_dashboard_widget)
```

## 2. Declaring and Rendering a Slot (For Hosts)

If you are building a new page and want to allow other modules to inject UI elements into it, you must declare the slot and render it.

```python
# src/modules/my_dashboard/router.py
from nicegui import ui
from src.core.hooks import hookimpl
from src.ui.page_slot_registry import page_slot_registry

@hookimpl
def register_ui():
    @ui.page('/my_dashboard')
    def my_dashboard_page():
        ui.label('Main Dashboard').classes('text-2xl')
        
        # 1. Provide a container for the plugins
        with ui.row().classes('w-full gap-4'):
            # 2. Render all injected components for this slot
            page_slot_registry.render('my_dashboard', 'widgets')
```

## Available UI Hooks

Aside from the `page_slot_registry`, modules can also register full applications to the sidebar using the `ui_registry`:

```python
from src.ui.registry import ui_registry

ui_registry.register_app(
    name="My Dashboard",
    icon="dashboard",
    route="/my_dashboard"
)
```
