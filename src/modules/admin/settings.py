from nicegui import ui
from src.ui.layout import MainLayout
from src.core.config import settings

@ui.page("/admin/settings")
def settings_editor_page():
    with MainLayout():
        with ui.column().classes("w-full gap-4 p-4"):
            with ui.row().classes("w-full items-center gap-4"):
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/admin")).props("flat")
                ui.label("System Settings").classes("text-3xl font-black")
            
            ui.label("Global framework configuration (from .env and Pydantic).").classes("text-slate-500")

            # Settings Form
            with ui.card().classes("w-full max-w-2xl p-6 gap-4"):
                ui.label("Core Configuration").classes("text-lg font-bold border-b pb-2")
                
                ui.input("Project Name", value=settings.PROJECT_NAME).classes("w-full").props("readonly")
                ui.input("API Prefix", value=settings.API_PREFIX).classes("w-full").props("readonly")
                
                ui.label("Database & Backend").classes("text-lg font-bold border-b pb-2 mt-4")
                ui.input("Mongo DSN", value=settings.MONGO_URL.split("@")[-1]).classes("w-full").props("readonly")
                ui.input("Redis URL", value=settings.REDIS_URL).classes("w-full").props("readonly")

                ui.label("Environment").classes("text-lg font-bold border-b pb-2 mt-4")
                ui.select(options=["DEBUG", "INFO", "WARNING", "ERROR"], value="INFO", label="Log Level").classes("w-full")

                with ui.row().classes("mt-6 justify-end w-full"):
                    ui.button("Save Changes", icon="save").props("elevated disabled")
                    ui.label("Read-only in demonstration mode.").classes("text-xs text-slate-400 italic")
