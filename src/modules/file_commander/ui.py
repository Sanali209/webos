from nicegui import ui
from src.ui.layout import MainLayout
from src.ui.registry import ui_registry, AppMetadata
from src.core.hooks import hookimpl
from src.core.storage import storage_manager

class FilePanel:
    def __init__(self, title: str, initial_path: str = "fs://local/"):
        self.title = title
        self.current_path = initial_path
        self.items = []
        self.selection = None
        
        with ui.column().classes("flex-grow border rounded-lg bg-white overflow-hidden"):
            # Header
            with ui.row().classes("w-full bg-slate-100 p-2 items-center border-b"):
                ui.icon("folder").classes("text-primary")
                self.path_label = ui.label(self.current_path).classes("font-mono text-xs flex-grow truncate")
                ui.button(icon="refresh", on_click=self.refresh).props("flat dense")

            # File List
            self.list_container = ui.column().classes("w-full p-2 h-96 overflow-y-auto gap-1")
        
        ui.timer(0.1, self.refresh, once=True)

    async def refresh(self):
        self.list_container.clear()
        try:
            items = await storage_manager.list_dir(self.current_path)
            for item in items:
                with ui.row().classes("w-full p-1 hover:bg-blue-50 cursor-pointer rounded text-sm items-center gap-2").on("click", lambda i=item: self.select(i)):
                    ui.icon("folder" if item.is_dir else "description").classes("text-slate-400")
                    ui.label(item.name).classes("flex-grow")
                    if not item.is_dir:
                        ui.label(f"{item.size // 1024} KB").classes("text-[10px] text-slate-400")
        except Exception as e:
            with self.list_container:
                ui.label(f"Error: {e}").classes("text-red-500 text-xs")

    def select(self, item):
        self.selection = item
        ui.notify(f"Selected: {item.name}")

@ui.page("/file-commander")
def file_commander_page():
    with MainLayout():
        with ui.column().classes("w-full gap-4 p-4"):
            ui.label("File Commander").classes("text-3xl font-black")
            ui.label("Dual-panel view of Local and S3 storage.").classes("text-slate-500")

            with ui.row().classes("w-full gap-4"):
                panel_a = FilePanel("Panel A", "fs://local/")
                
                # Center Actions
                with ui.column().classes("justify-center gap-2"):
                    ui.button(icon="arrow_forward").props("outline dense")
                    ui.button(icon="arrow_back").props("outline dense")
                
                panel_b = FilePanel("Panel B", "fs://local/test_folder/")

@hookimpl
def register_ui():
    """Register the File Commander App."""
    ui_registry.register_app(AppMetadata(
        name="File Explorer",
        icon="folder",
        route="/file-commander",
        description="Browse and manage files across Local and S3 storage.",
        commands=["browse files", "local storage", "s3 storage", "file transfer"]
    ))
toxicology_report = "File Commander UI initialized"
