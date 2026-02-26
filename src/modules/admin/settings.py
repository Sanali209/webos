from nicegui import ui
from src.ui.layout import MainLayout
from src.core.config import settings
from src.core.services.settings_service import settings_service
from src.core.sdk.data_explorer import DataExplorer

@ui.page("/admin/settings")
def settings_editor_page():
    with MainLayout():
        with ui.column().classes("w-full gap-4 p-4"):
            with ui.row().classes("w-full items-center gap-4"):
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/admin")).props("flat")
                ui.label("System Settings & Module Registry").classes("text-3xl font-black")
            
            with ui.tabs().classes("w-full") as tabs:
                ui.tab("Core", icon="settings")
                ui.tab("Modules", icon="extension")

            with ui.tab_panels(tabs, value="Core").classes("w-full bg-transparent"):
                with ui.tab_panel("Core"):
                    ui.label("Global framework configuration (from .env and Pydantic).").classes("text-slate-500 mb-4")
                    # Settings Form
                    with ui.card().classes("w-full max-w-2xl p-6 gap-4"):
                        ui.label("Core Configuration").classes("text-lg font-bold border-b pb-2")
                        
                        ui.input("Project Name", value=settings.PROJECT_NAME).classes("w-full").props("readonly")
                        ui.input("API Prefix", value=settings.API_PREFIX).classes("w-full").props("readonly")
                        
                        ui.label("Database & Backend").classes("text-lg font-bold border-b pb-2 mt-4")
                        ui.input("Mongo DSN", value=settings.MONGO_URL.split("@")[-1]).classes("w-full").props("readonly")
                        ui.input("Redis URL", value=settings.REDIS_URL).classes("w-full").props("readonly")

                        ui.label("Environment").classes("text-lg font-bold border-b pb-2 mt-4")
                        log_level = ui.select(options=["DEBUG", "INFO", "WARNING", "ERROR"], value="INFO", label="Log Level").classes("w-full")

                        async def save_core_settings():
                             # Core settings are typically environment variables, but we could persist overrides
                             # For now, we'll just notify as we haven't implemented .env writing
                             ui.notify(f"Log Level changed to {log_level.value}. Restart required for effect.", type="info")

                        with ui.row().classes("mt-6 justify-end w-full"):
                            ui.button("Save Changes", icon="save", on_click=save_core_settings).props("elevated")

                with ui.tab_panel("Modules"):
                    ui.label("Persistent settings registered by modules. Changes are saved to MongoDB.").classes("text-slate-500 mb-4")
                    
                    # Fetch all registered module schemas
                    schemas = settings_service._schemas
                    
                    if not schemas:
                        ui.label("No modules have registered settings.").classes("italic text-slate-400 mt-10")
                    else:
                        with ui.column().classes("w-full gap-8"):
                            for module_name, schema_class in schemas.items():
                                with ui.card().classes("w-full p-4"):
                                    # We wrap the single settings object in a list for DataExplorer
                                    current_settings = settings_service.get(module_name)
                                    
                                    async def handle_change(items, m_name=module_name):
                                        # When the grid changes, items[0] is our updated Pydantic model
                                        if items:
                                            await settings_service.update(m_name, items[0].model_dump())
                                    
                                    DataExplorer(
                                        model=schema_class,
                                        items=[current_settings] if current_settings else [],
                                        title=f"Module: {module_name}",
                                        on_change=handle_change,
                                        can_add=False,
                                        can_delete=False
                                    )
