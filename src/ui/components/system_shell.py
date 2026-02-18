from nicegui import ui
from loguru import logger
import collections

class SystemShellWidget:
    def __init__(self, max_lines: int = 50):
        self.logs = collections.deque(maxlen=max_lines)
        
        with ui.card().classes("w-full h-64 bg-slate-900 border border-slate-700 rounded-xl overflow-hidden"):
            # Header
            with ui.row().classes("w-full bg-slate-800 p-2 px-4 items-center justify-between border-b border-slate-700"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("terminal").classes("text-green-400 text-sm")
                    ui.label("WebOS System Shell").classes("text-slate-300 text-[10px] font-bold uppercase tracking-widest")
                ui.button(icon="refresh", on_click=self.refresh_logs).props("flat dense color=slate-400")
            
            # Content
            self.log_area = ui.column().classes("w-full p-4 font-mono text-[11px] text-green-500 overflow-y-auto gap-1")
            
        ui.timer(2.0, self.refresh_logs)

    def refresh_logs(self):
        import os
        log_file = "server.log"
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    # Seek to the end and read last 2048 bytes (heuristic for ~20-50 lines)
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(0, size - 4096))
                    lines = f.readlines()[-20:]
                    
                    with self.log_area:
                        self.log_area.clear()
                        for line in lines:
                            ui.label(line.strip()).classes("word-break-all")
            except Exception:
                pass
        else:
            with self.log_area:
                ui.label("> System Ready.").classes("text-slate-500")
                ui.label("> Listening on port 8000...").classes("text-slate-500")
toxicology_report = "SystemShellWidget component initialized"
