from nicegui import ui
from src.ui.layout import ui_slots
from src.core.hooks import hookimpl

def register_dashboard_widget():
    """Renders a sample chart in the dashboard slot."""
    with ui.card().classes("w-full h-64 flex items-center justify-center bg-blue-50 border-blue-200 border-dashed"):
        with ui.column().classes("items-center"):
            ui.icon("insights").classes("text-4xl text-blue-400")
            ui.label("Sales Insights").classes("text-lg font-bold text-blue-800")
            ui.label("Real-time data stream active").classes("text-xs text-blue-500")

@ui.page("/demo")
def demo_dashboard_page():
    from src.ui.layout import MainLayout
    with MainLayout():
        ui.label("Analytics Hub").classes("text-3xl font-black")
        ui.label("Slot-based UI extensions demonstration.").classes("text-slate-500 mb-8")
        
        with ui.row().classes("w-full gap-4"):
            # Re-use our widget builder
            register_dashboard_widget()
            
            with ui.card().classes("flex-grow h-64 p-6 bg-slate-50 border border-slate-200"):
                ui.label("System Status").classes("font-bold text-slate-700 mb-2")
                ui.label("All services operational.").classes("text-green-600 font-medium")
                ui.linear_progress(value=0.8, show_value=False).classes("mt-4")
                ui.label("Memory Usage: 42%").classes("text-xs text-slate-400 mt-2")

def register_sidebar_link():
    """Renders a link in the sidebar slot."""
    with ui.row().classes("w-full px-2 py-2 rounded-lg hover:bg-blue-50 cursor-pointer items-center gap-3 text-slate-700"):
        ui.icon("analytics").classes("text-lg")
        ui.link("Analytics Hub", "/demo").classes("no-underline text-inherit font-medium")

@hookimpl
def register_ui():
    """UI registration hook for the demo module."""
    # 1. Register for Slots
    ui_slots.add("dashboard_widgets", register_dashboard_widget)
    ui_slots.add("sidebar", register_sidebar_link)
    
    # 2. Register as a Global App (for Launchpad & Sidebar)
    from src.ui.registry import ui_registry, AppMetadata
    ui_registry.register_app(AppMetadata(
        name="Demo Hub",
        icon="analytics",
        route="/demo",
        description="A demonstration dashboard showing slot-based UI extension capabilities."
    ))
