from nicegui import ui
from taskiq import TaskiqResult
import asyncio

class TaskProgressWidget:
    """
    A NiceGUI component that tracks and displays the progress of a TaskIQ task.
    """
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.container = ui.card().classes("w-full p-4 gap-2")
        with self.container:
            ui.label(f"Task: {task_id[:8]}...").classes("text-sm font-bold")
            self.progress_bar = ui.linear_progress(value=0, show_value=False).classes("w-full")
            self.status_label = ui.label("Queueing...").classes("text-xs text-slate-500")
        
        # Start polling
        ui.timer(1.0, self.update_status)

    async def update_status(self):
        from src.core.tasks import broker
        try:
            # get_result without timeout results in ResultIsMissingError or None if not ready
            result = await broker.result_backend.get_result(self.task_id)
            
            if result:
                self.progress_bar.set_value(1.0)
                self.status_label.set_text("Complete!")
                self.status_label.classes(replace="text-green-600")
                ui.notify(f"Task {self.task_id[:8]} finished!")
                return False # Stop timer
        except Exception:
            pass # Handle as "not ready yet" below

        # If we reach here, the task is either missing or still running
        self.status_label.set_text("Running...")
        self.progress_bar.classes("indeterminate")
