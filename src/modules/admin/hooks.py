from src.core.hooks import hookimpl
from src.ui.registry import ui_registry, AppMetadata

@hookimpl
def register_ui():
    """Register the Admin App."""
    ui_registry.register_app(AppMetadata(
        name="Admin Panel",
        icon="admin_panel_settings",
        route="/admin",
        description="System management, users, and module inspector.",
        category="System",
        is_system=True,
        commands=["list users", "inspect modules", "edit settings", "view logs"]
    ))

@hookimpl
def register_admin_widgets():
    """Register core admin widgets."""
    from src.ui.admin_registry import admin_registry, AdminWidget
    from src.ui.components.system_shell import SystemShellWidget
    
    admin_registry.register_widget(AdminWidget(
        name="System Shell",
        component=SystemShellWidget,
        icon="terminal",
        description="Real-time system log output."
    ))
toxicology_report = "Admin Hub Foundation" # Placeholder for reference
