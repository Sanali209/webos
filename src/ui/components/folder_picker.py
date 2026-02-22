from nicegui import ui
from src.core.storage import storage_manager
from typing import Callable
import os

class FolderPicker(ui.dialog):
    def __init__(self, callback: Callable[[str], None], base_path: str = "fs://local/"):
        super().__init__()
        self.callback = callback
        self.current_path = base_path
        
        with self, ui.card().classes("w-full max-w-2xl p-0 overflow-hidden"):
            # Header
            with ui.row().classes("w-full bg-primary text-white p-4 items-center"):
                ui.icon("folder", size="sm")
                ui.label("Select Watch Folder").classes("text-lg font-bold flex-grow")
                ui.button(icon="close", on_click=self.close).props("flat color=white")
            
            # Browser Context
            with ui.column().classes("p-4 gap-2 w-full"):
                with ui.row().classes("w-full items-center gap-2"):
                    ui.button(icon="arrow_upward", on_click=self.navigate_up).props("flat dense color=primary").tooltip("Go Up")
                    self.path_label = ui.label(self.current_path).classes("font-mono text-sm text-slate-700 flex-grow pr-2 truncate")
                
                ui.separator()
                
                # List of directories
                self.list_container = ui.column().classes("w-full h-80 overflow-y-auto border rounded bg-slate-50")
                
                ui.separator()
                
                with ui.row().classes("w-full justify-end pt-2"):
                    ui.button("Cancel", on_click=self.close).props("flat color=slate")
                    ui.button("Select This Folder", on_click=self.confirm_selection).props("color=primary")

            ui.timer(0.1, self.refresh, once=True)

    def navigate_up(self):
        # Prevent navigating above fs://local/ (the root prefix in AFS)
        if self.current_path in ("fs://local/", "fs://local"):
            ui.notify("Already at root directory", type="warning")
            return
            
        # Example: fs://local/Users/name/ -> fs://local/Users/
        parts = self.current_path.rstrip('/').split('/')
        if len(parts) <= 3: # fs: , , local
            self.current_path = "fs://local/"
        else:
            self.current_path = '/'.join(parts[:-1]) + '/'
            
        asyncio = __import__('asyncio')
        asyncio.create_task(self.refresh())

    def navigate_down(self, folder_name: str):
        # Ensure trailing slash
        if not self.current_path.endswith('/'):
            self.current_path += '/'
        self.current_path += folder_name + '/'
        
        asyncio = __import__('asyncio')
        asyncio.create_task(self.refresh())

    async def refresh(self):
        self.list_container.clear()
        self.path_label.text = self.current_path
        
        try:
            items = await storage_manager.list_dir(self.current_path)
            # Only show directories for folder picker
            directories = [item for item in items if item.is_dir]
            
            # Sort alphabetically
            directories.sort(key=lambda x: x.name.lower())
            
            with self.list_container:
                if not directories:
                    ui.label("Empty directory").classes("p-4 text-slate-400 italic text-center w-full")
                else:
                    for item in directories:
                        with ui.row().classes("w-full p-2 hover:bg-slate-200 cursor-pointer items-center gap-3 border-b border-slate-100").on("click", lambda i=item: self.navigate_down(i.name)):
                            ui.icon("folder").classes("text-primary")
                            ui.label(item.name).classes("word-break-all text-slate-700")
        except Exception as e:
            with self.list_container:
                ui.label(f"Error accessing directory: {e}").classes("p-4 text-red-500 w-full text-center")

    def confirm_selection(self):
        # We assume local paths for watcher service right now. Convert URN to local path.
        if self.current_path.startswith("fs://local/"):
            local_path = self.current_path[11:]
            # Ensure it starts with root if on linux, or drive letter on windows
            # Just passing it as is, Watchdog will need a valid absolute path.
            # Local AFS source typically expects absolute paths after `fs://local/`.
            # Let's pass the raw URN or Local Path depending on the caller.
            # WatcherService usually wants a string path. We'll give it the absolute local path.
            # For Windows, fs://local/D:/github becomes D:/github
            
            # Simple heuristic
            if local_path.startswith('/'):
                pass
            
            # Just pass the URN's payload path. The caller can convert it to Path
            self.callback(local_path)
            self.close()
        else:
            ui.notify("Only local file system paths are supported for watch folders.", type="negative")
