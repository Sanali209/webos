from typing import Callable, Dict, List
from nicegui import app, ui
from .theme import theme

class UI_Slot:
    """Registry for UI components that wish to be injected into specific layout areas."""
    
    def __init__(self):
        # Maps slot_name -> list of builder functions
        self._slots: Dict[str, List[Callable]] = {
            "sidebar": [],
            "header": [],
            "dashboard_widgets": [],
            "app_grid": [],
            "asset_picker_overlay": [],
            "command_palette_actions": []
        }

    def add(self, slot_name: str, builder: Callable, module: str = "core"):
        """Register a builder function for a specific slot."""
        if slot_name not in self._slots:
            self._slots[slot_name] = []
        self._slots[slot_name].append(builder)

    def render(self, slot_name: str, **kwargs):
        """Execute all registered builders for a specific slot, optionally passing kwargs."""
        if slot_name in self._slots:
            for builder in self._slots[slot_name]:
                try:
                    builder(**kwargs)
                except Exception as e:
                    import traceback
                    print(f"Error rendering slot {slot_name}: {e}")
                    traceback.print_exc()

from src.ui.registry import ui_registry

# Global slot registry
ui_slots = UI_Slot()

class MainLayout:
    """The root UI shell for WebOS."""
    
    def __init__(self):
        self.drawer = None

    def render_app_card(self, app):
        """Renders a single app icon/card for the Launchpad."""
        card = ui.card().classes("cursor-pointer hover:scale-105 transition-all duration-300 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col items-center justify-center gap-3 w-full aspect-square relative")
        with card:
            # Badge Overlay
            if app.badge_text:
                ui.label(app.badge_text).classes("absolute top-2 right-2 bg-primary text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm z-10 uppercase tracking-wider")
            
            ui.icon(app.icon).classes("text-5xl text-primary mb-2")
            ui.label(app.name).classes("text-lg font-bold text-slate-800 text-center uppercase tracking-wider")
            if app.description:
                ui.label(app.description).classes("text-xs text-slate-400 text-center line-clamp-2")
        
        # Click to navigate - explicit closure
        card.on("click", lambda: ui.navigate.to(app.route))

    async def logout(self):
        app.storage.user.clear()
        ui.notify("Logged out successfully")
        ui.navigate.to("/login")

    def __enter__(self):
        """Standard context manager entry."""
        # Restore user context from NiceGUI session if available
        from src.core.middleware import user_id_context
        from loguru import logger
        
        # logger.debug(f"DEBUG: app.storage.user contents: {dict(app.storage.user)}")
        if "user_id" in app.storage.user:
            uid = app.storage.user["user_id"]
            user_id_context.set(uid)
            logger.debug(f"Restored user_id_context: {uid}")
        else:
            logger.debug("No user_id found in app.storage.user")

        # Header
        with ui.header().classes("bg-white text-slate-900 border-b border-slate-200 py-2 px-4 shadow-none fade-in").style("height: 64px"):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-4"):
                    ui.button(on_click=lambda: self.drawer.toggle(), icon="menu").props("flat round color=primary")
                    ui.link("WebOS", "/").classes("text-xl font-bold tracking-tight text-primary no-underline")
                
                with ui.row().classes("items-center gap-2"):
                    # Render Header Slots (e.g., Quick actions, User Avatar)
                    ui_slots.render("header")
                    ui.button(on_click=theme.toggle_dark_mode, icon="dark_mode").props("flat round")
                    ui.button(on_click=lambda: self.command_palette.open(), icon="search").props("flat round color=primary").classes("ml-2")
                    
                    if "user_id" in app.storage.user:
                        with ui.row().classes("items-center gap-2"):
                            ui.label("Admin").classes("text-xs font-bold text-slate-400 uppercase tracking-widest")
                            ui.button(on_click=self.logout, icon="logout").props("flat round color=red").classes("ml-1")
                    else:
                        ui.button("Login", on_click=lambda: ui.navigate.to("/login"), icon="login").props("flat color=primary").classes("px-4 rounded-xl font-bold")
        
        # Global Key Listener (Ctrl+K)
        ui.keyboard(on_key=self.handle_key)
        
        # Sidebar (Drawer)
        with ui.left_drawer(value=True).classes("bg-slate-50 border-r border-slate-200 px-0 shadow-xl") as self.drawer:
            with ui.column().classes("w-full p-4 gap-2"):
                ui.label("NAVIGATOR").classes("text-[10px] font-black text-slate-400 mb-2 px-2 tracking-[0.2em]")
                
                # Standard Dashboard Link
                with ui.row().classes("w-full px-2 py-2 rounded-xl hover:bg-slate-100 cursor-pointer items-center gap-3 text-slate-700 transition-colors"):
                    ui.icon("dashboard").classes("text-lg")
                    ui.link("Dashboard", "/").classes("no-underline text-inherit font-semibold text-sm")

                # Dynamic Links from Registry
                for app_meta in ui_registry.apps:
                    with ui.link(target=app_meta.route).classes("w-full no-underline"):
                        with ui.row().classes("w-full px-2 py-2 rounded-xl hover:bg-slate-100 cursor-pointer items-center gap-3 text-slate-700 transition-colors"):
                            ui.icon(app_meta.icon).classes("text-lg")
                            ui.label(app_meta.name).classes("font-semibold text-sm")

                # Render Sidebar Slots (Manual Module Navigation)
                ui_slots.render("sidebar")

        # Main Content
        self.render_command_palette()
        
        # Render invisible global overlays (like asset picker)
        ui_slots.render("asset_picker_overlay")
        
        self.content_container = ui.column().classes("w-full max-w-7xl mx-auto p-8 gap-8")
        self.content_container.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Standard context manager exit."""
        self.content_container.__exit__(exc_type, exc_val, exc_tb)

    def __call__(self, content_builder: Callable = None):
        """renders the common shell and then the specific page content."""
        with self:
            if content_builder:
                content_builder()
            else:
                # Default Landing Page (Dashboard / Launchpad)
                with ui.column().classes("gap-1 mb-4"):
                    ui.label("Good Morning, User").classes("text-4xl font-black text-slate-800 tracking-tight")
                    ui.label("WebOS Shell v0.1 ready for mission-critical tasks.").classes("text-slate-400 font-medium")
                
                ui.label("LAUNCHPAD").classes("text-[10px] font-black text-slate-400 mt-4 tracking-[0.2em]")
                with ui.grid(columns=4).classes("w-full gap-6"):
                    # Render Apps from Registry
                    for app_meta in ui_registry.apps:
                        self.render_app_card(app_meta)
                    
                    # Render App Grid Slots (Manual Extension)
                    ui_slots.render("app_grid")
                    
                ui.label("ACTIVE WIDGETS").classes("text-[10px] font-black text-slate-400 mt-12 tracking-[0.2em]")
                with ui.row().classes("w-full gap-6 flex-wrap"):
                    # Render Dashboard Widgets
                    ui_slots.render("dashboard_widgets")


    def handle_key(self, e):
        """Global hotkey handler."""
        if e.key == "k" and e.modifiers.ctrl:
            self.command_palette.open()

    def render_command_palette(self):
        """Renders the HUD / Command Palette."""
        with ui.dialog() as self.command_palette, ui.card().classes("w-full max-w-2xl p-0 overflow-hidden"):
            with ui.column().classes("w-full"):
                # Search Bar
                with ui.row().classes("w-full p-4 items-center gap-4 border-b"):
                    ui.icon("terminal").classes("text-2xl text-primary")
                    search_input = ui.input(placeholder="Search apps or type a command...").props("autofocus borderless").classes("flex-grow text-lg")
                    ui.label("ESC to close").classes("text-[10px] text-slate-400 uppercase font-bold")
                
                # Results Area
                results_container = ui.column().classes("w-full p-2 max-h-96 overflow-y-auto")
                
                def update_results():
                    results_container.clear()
                    query = search_input.value.lower()
                    if not query:
                        return
                    
                    found = 0
                    for app in ui_registry.apps:
                        if query in app.name.lower() or query in app.description.lower() or any(query in cmd.lower() for cmd in app.commands):
                            with results_container:
                                with ui.row().classes("w-full p-3 hover:bg-slate-100 cursor-pointer rounded-xl items-center gap-4").on("click", lambda a=app: [self.command_palette.close(), ui.navigate.to(a.route)]):
                                    ui.icon(app.icon).classes("text-xl text-slate-400")
                                    with ui.column().classes("gap-0"):
                                        ui.label(app.name).classes("font-bold text-slate-800")
                                        ui.label(app.description).classes("text-xs text-slate-400")
                                    ui.space()
                                    ui.label("RETURN").classes("text-[10px] bg-slate-100 px-1 rounded font-bold text-slate-400")
                            found += 1
                    
                    if found == 0:
                        with results_container:
                            ui.label("No results found").classes("p-4 text-slate-400 italic text-center w-full")

                search_input.on("update:model-value", update_results)

# Global Layout Instance
layout = MainLayout()
