from nicegui import ui
from src.ui.admin_registry import AdminWidget

def render_dam_admin_widget():
    with ui.card().classes("w-full h-full p-6 shadow-sm border border-slate-200 col-span-2 rounded-2xl bg-white"):
        with ui.row().classes("w-full items-center justify-between border-b border-slate-100 pb-4 mb-4"):
            with ui.row().classes("items-center gap-3"):
                ui.icon("analytics").classes("text-primary text-2xl bg-blue-50 p-2 rounded-xl")
                with ui.column().classes("gap-0"):
                    ui.label('DAM Pipeline Diagnostics').classes("text-lg font-black text-slate-800 tracking-tight")
                    ui.label('System-wide media processing statistics').classes("text-xs text-slate-400 font-medium")
            ui.button("Reprocess Errors", on_click=lambda: ui.notify("Reprocessing error queue...", type="warning")).props("outline color=red rounded font-bold px-4")
            
        stats_container = ui.row().classes("w-full gap-12 mt-2")
        
        async def load_stats():
            from src.modules.dam.models import Asset, AssetStatus
            stats_container.clear()
            try:
                total = await Asset.find_all().count()
                processed = await Asset.find({"status": AssetStatus.READY}).count()
                processing = await Asset.find({"status": AssetStatus.PROCESSING}).count()
                errors = await Asset.find({"status": AssetStatus.ERROR}).count()
                
                with stats_container:
                    def stat_box(label, count, total_ref=None, color="slate"):
                        with ui.column().classes("gap-1"):
                            ui.label(label).classes(f"text-[10px] font-black text-{color}-400 uppercase tracking-widest")
                            with ui.row().classes("items-baseline gap-2"):
                                ui.label(f"{count:,}").classes(f"text-4xl font-black text-{color}-700 tracking-tighter")
                                if total_ref and total_ref > 0:
                                    pct = (count/total_ref)*100
                                    ui.label(f"{pct:.1f}%").classes(f"text-xs font-bold text-{color}-500")
                            
                    stat_box("Total Catalog", total)
                    stat_box("Fully Indexed", processed, total, "green")
                    stat_box("In Pipeline", processing, total, "blue")
                    stat_box("Failed Items", errors, total, "red")
                    
            except Exception as e:
                with stats_container:
                    ui.label(f"Data Source Error: {e}").classes("text-red-500 font-bold bg-red-50 p-4 rounded-xl w-full")

        ui.timer(0.1, load_stats, once=True)

def DAMAdminWidget() -> AdminWidget:
    return AdminWidget(
        name="DAM Pipeline",
        component=render_dam_admin_widget,
        icon="analytics",
        description="Statistics and controls for DAM AI background processes",
        column_span=2
    )

