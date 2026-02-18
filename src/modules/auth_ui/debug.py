from nicegui import app, ui
from src.ui.layout import MainLayout
from src.core.middleware import user_id_context

@ui.page("/debug/auth")
def debug_auth_page():
    with MainLayout():
        ui.label("Auth Debugger").classes("text-2xl font-bold")
        
        with ui.card().classes("p-4 w-full max-w-lg"):
            ui.label("Session Information").classes("font-bold underline")
            ui.label(f"user_id in storage: {app.storage.user.get('user_id')}")
            ui.label(f"user_id_context: {user_id_context.get()}")
            
            ui.label("Raw Storage:").classes("mt-4 font-bold")
            ui.label(str(dict(app.storage.user)))
            
        ui.button("Clear Session", on_click=lambda: [app.storage.user.clear(), ui.notify("Session cleared"), ui.navigate.to("/debug/auth")])
        ui.button("Refresh Page", on_click=lambda: ui.navigate.to("/debug/auth")).classes("ml-2")
