from nicegui import ui
from src.core.hooks import hookimpl
from src.ui.layout import ui_slots
from src.ui.registry import ui_registry, AppMetadata
from src.ui.components.task_widget import TaskProgressWidget
from .tasks import generate_report_task
from loguru import logger

@ui.page("/demo/report")
def report_page():
    from src.ui.layout import MainLayout
    with MainLayout():
        ui.label("Report Generation Hub").classes("text-3xl font-black")
        ui.label("Trigger long-running PDF generations and track them in real-time.").classes("text-slate-500")

        input_name = ui.input("Report Name", value="Monthly_Sales_Feb").classes("w-full max-w-sm")
        
        async def start_task():
            name = input_name.value
            task = await generate_report_task.kiq(name)
            ui.notify(f"Task started: {task.task_id[:8]}")
            with task_container:
                TaskProgressWidget(task.task_id)

        ui.button("Start Generation", on_click=start_task).props("elevated")
        
        ui.label("Active Tasks").classes("text-lg font-bold mt-8")
        task_container = ui.column().classes("w-full gap-4")

@hookimpl
def register_ui():
    """Register the Report Demo app."""
    ui_registry.register_app(AppMetadata(
        name="Report Hub",
        icon="summarize",
        route="/demo/report",
        description="Background task demonstration with real-time feedback."
    ))
