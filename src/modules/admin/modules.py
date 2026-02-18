from nicegui import ui
from src.ui.layout import MainLayout
from src.core.module_loader import loader

@ui.page("/admin/modules")
def module_inspector_page():
    with MainLayout():
        with ui.column().classes("w-full gap-4 p-4"):
            with ui.row().classes("w-full items-center gap-4"):
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/admin")).props("flat")
                ui.label("Module Inspector").classes("text-3xl font-black")
            
            ui.label("System plugins currently active in the WebOS kernel.").classes("text-slate-500")

            # Module List
            with ui.grid(columns=2).classes("w-full gap-4"):
                for mod_name in sorted(loader.loaded_modules):
                    with ui.card().classes("w-full"):
                        with ui.row().classes("items-center justify-between w-full p-2 bg-slate-100 border-b"):
                            ui.label(mod_name).classes("font-mono font-bold")
                            ui.badge("LOADED", color="green")
                        
                        # Module Details (Mocking some metadata for now)
                        with ui.column().classes("p-4"):
                            ui.label(f"Path: src.modules.{mod_name}").classes("text-xs text-slate-400")
                            ui.label("Hooks Detected: register_ui, register_models").classes("text-xs mt-2")
                            
                            with ui.row().classes("mt-4 gap-2"):
                                ui.button("Disable", icon="block", color="red").props("small outline")
                                ui.button("Reload", icon="refresh").props("small outline")
