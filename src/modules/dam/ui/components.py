from nicegui import ui
from src.ui.layout import ui_slots
from .upload_dialog import upload_dropzone_dialog

def dam_quick_upload_button():
    """Renders a cloud upload button in the header that opens the dropzone."""
    dialog = upload_dropzone_dialog()
    ui.button(on_click=dialog.open, icon="cloud_upload").props("flat round text-color=primary").tooltip("Upload to Media Library")

def dam_storage_widget():
    """Renders a dashboard card showing DAM storage statistics."""
    with ui.card().classes("w-64 p-6 shadow-sm border border-slate-200"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Media Library").classes("font-bold text-slate-700")
            ui.icon("photo_library", color="primary", size="1.5rem")
        
        with ui.column().classes("mt-4 gap-0"):
            count_label = ui.label("...").classes("text-4xl font-black text-slate-800 tracking-tight")
            ui.label("TOTAL ASSETS").classes("text-[10px] text-slate-400 font-bold uppercase tracking-widest")
            
        async def load_stats():
            try:
                from src.modules.dam.models import Asset
                count = await Asset.find_all().count()
                count_label.set_text(f"{count:,}")
            except Exception as e:
                import loguru
                loguru.logger.error(f"Failed to load DAM stats: {e}")
                count_label.set_text("ERR")
                
        ui.timer(0.1, load_stats, once=True)

def dam_asset_picker_overlay():
    pass

def register_global_slots():
    ui_slots.add("header", dam_quick_upload_button, module="dam")
    ui_slots.add("dashboard_widgets", dam_storage_widget, module="dam")
    ui_slots.add("asset_picker_overlay", dam_asset_picker_overlay, module="dam")

