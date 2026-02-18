from nicegui import ui
from src.ui.layout import MainLayout
from src.ui.admin_registry import admin_registry
from . import users, modules, settings

@ui.page("/admin")
def admin_page():
    with MainLayout():
        with ui.column().classes("w-full gap-6 p-4"):
            # Header
            with ui.row().classes("w-full items-center justify-between"):
                ui.label("Admin Dashboard").classes("text-3xl font-black")
                ui.button("Refresh Results", icon="refresh", on_click=lambda: ui.notify("Refreshed")).props("flat")

            # Widget Grid
            ui.label("System Extensions").classes("text-xl font-bold mt-4")
            widgets = admin_registry.get_widgets()
            
            if not widgets:
                ui.label("No admin widgets registered.").classes("italic text-slate-500")
            else:
                with ui.grid(columns=3).classes("w-full gap-4"):
                    for widget in widgets:
                        with ui.card().classes("w-full hover:shadow-lg transition-shadow"):
                            with ui.row().classes("items-center gap-2 p-2 bg-slate-50 border-b w-full"):
                                ui.icon(widget.icon).classes("text-primary")
                                ui.label(widget.name).classes("font-bold")
                            
                            # Render the component
                            widget.component()
                            
                            if widget.description:
                                ui.label(widget.description).classes("text-xs text-slate-400 p-2 italic")

            # Admin Management Tabs
            ui.label("Management Tools").classes("text-xl font-bold mt-8")
            with ui.grid(columns=3).classes("w-full gap-4"):
                with ui.card().classes("cursor-pointer bg-blue-50").on("click", lambda: ui.navigate.to("/admin/users")):
                    ui.icon("people").classes("text-2xl mb-2")
                    ui.label("User Manager").classes("font-bold")
                    ui.label("Manage users, roles, and permissions.").classes("text-xs")

                with ui.card().classes("cursor-pointer bg-green-50").on("click", lambda: ui.navigate.to("/admin/modules")):
                    ui.icon("extension").classes("text-2xl mb-2")
                    ui.label("Module Inspector").classes("font-bold")
                    ui.label("View loaded plugins and registered hooks.").classes("text-xs")

                with ui.card().classes("cursor-pointer bg-orange-50").on("click", lambda: ui.navigate.to("/admin/settings")):
                    ui.icon("settings").classes("text-2xl mb-2")
                    ui.label("System Settings").classes("font-bold")
                    ui.label("Configure framework environment variables.").classes("text-xs")
