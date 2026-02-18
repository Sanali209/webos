from src.core.hooks import hookimpl
from src.ui.registry import ui_registry, AppMetadata
from src.ui.admin_registry import admin_registry, AdminWidget
from nicegui import ui

@hookimpl
def register_ui():
    """Register the Demo Dashboard App."""
    pass

@hookimpl
def register_admin_widgets():
    """Demonstrate extending the admin panel from another module."""
    
    def sales_summary():
        with ui.column().classes("p-4"):
            ui.label("Sales Summary (Mock)").classes("font-bold text-blue-600")
            ui.label("$12,450.00").classes("text-2xl font-black")
            ui.label("+15% vs last month").classes("text-xs text-green-500")

    admin_registry.register_widget(AdminWidget(
        name="Sales Overview",
        component=sales_summary,
        icon="trending_up",
        description="Injected by demo_dashboard module."
    ))
toxicology_report = "Dashboard Extensibility Demo" # Placeholder
