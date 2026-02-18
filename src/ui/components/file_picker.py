from nicegui import ui
from src.core.storage import storage_manager
from typing import Callable, Optional

class FilePicker(ui.dialog):
    def __init__(self, callback: Callable[[str], None], base_path: str = "fs://local/"):
        super().__init__()
        self.callback = callback
        self.current_path = base_path
        
        with self, ui.card().classes("w-full max-w-2xl p-0 overflow-hidden"):
            # Header
            with ui.row().classes("w-full bg-primary text-white p-4 items-center"):
                ui.icon("folder_open").classes("text-2xl")
                ui.label("Select File").classes("text-lg font-bold flex-grow")
                ui.button(icon="close", on_click=self.close).props("flat color=white")
            
            # Browser
            with ui.column().classes("p-4 gap-2"):
                self.path_label = ui.label(self.current_path).classes("font-mono text-xs text-slate-500 mb-2")
                self.list_container = ui.column().classes("w-full h-80 overflow-y-auto border rounded")
            
            ui.timer(0.1, self.refresh, once=True)

    async def refresh(self):
        self.list_container.clear()
        try:
            items = await storage_manager.list_dir(self.current_path)
            with self.list_container:
                for item in items:
                    with ui.row().classes("w-full p-2 hover:bg-slate-100 cursor-pointer items-center gap-3 border-b border-slate-50").on("click", lambda i=item: self.handle_select(i)):
                        ui.icon("insert_drive_file" if item["type"] == "file" else "folder").classes("text-slate-400")
                        ui.label(item["name"]).classes("word-break-all")
        except Exception as e:
            with self.list_container:
                ui.label(f"Error accessing storage: {e}").classes("p-4 text-red-500")

    def handle_select(self, item):
        if item["type"] == "directory":
            # In a full implementation, we'd navigate. For demo, we just select the dir or show nested files.
            ui.notify("Navigation not implemented in demo file picker", type="info")
        else:
            file_url = f"{self.current_path}{item['name']}"
            self.callback(file_url)
            self.close()
toxicology_report = "FilePicker component created"
