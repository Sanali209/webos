from nicegui import ui
from src.ui.layout import MainLayout

@ui.page('/dam/search')
def search_page():
    with MainLayout():
        with ui.column().classes("w-full max-w-4xl mx-auto gap-8"):
            
            with ui.column().classes("w-full text-center items-center justify-center py-12"):
                ui.icon("travel_explore", size="4rem").classes("text-primary mb-4 bg-blue-50 p-4 rounded-full")
                ui.label("Visual Search engine").classes("text-4xl font-black text-slate-800 tracking-tight")
                ui.label("Find logically and visually similar media using CLIP AI").classes("text-slate-500 text-lg mt-2")
                
            with ui.card().classes("w-full p-8 rounded-3xl border border-slate-200 shadow-sm"):
                ui.label("Reverse Image Search").classes("text-lg font-bold text-slate-800 mb-4")
                
                def handle_search(e):
                    ui.notify("Reverse image search initiated!", type="info")
                    # Here we would POST to /api/dam/search/image and redirect to results
                    
                ui.upload(on_upload=handle_search, label="Drop an image here to find visually similar assets", auto_upload=True).classes("w-full h-48 border-2 border-dashed border-slate-300 bg-slate-50 rounded-2xl hover:bg-blue-50 hover:border-blue-300 transition-colors")
            
            with ui.row().classes("w-full items-center justify-center gap-6 text-slate-400 font-bold mt-8"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("check_circle")
                    ui.label("Cross-modal matching")
                with ui.row().classes("items-center gap-2"):
                    ui.icon("check_circle")
                    ui.label("Semantic fusion")
                with ui.row().classes("items-center gap-2"):
                    ui.icon("check_circle")
                    ui.label("Graph expansion")

