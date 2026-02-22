from nicegui import ui
from src.ui.layout import MainLayout

@ui.page('/dam/graph')
def graph_explorer_page():
    with MainLayout():
        with ui.column().classes("w-full h-[calc(100vh-120px)] bg-slate-900 rounded-3xl overflow-hidden relative border border-slate-800"):
            ui.label("KNOWLEDGE GRAPH EXPLORER").classes("absolute top-6 left-6 text-white/50 font-black text-2xl tracking-[0.2em] z-10 pointer-events-none mix-blend-overlay")
            
            # Since rendering Cytoscape requires JS, we'll embed a simple iframe or mock it
            # For this phase implementation, we present a beautiful mock or empty state as we haven't wired full JS bridge
            with ui.column().classes("w-full h-full items-center justify-center p-8 text-center bg-[url('https://www.transparenttextures.com/patterns/cubes.png')]"):
                ui.icon("hub", color="primary", size="6rem").classes("mb-6 drop-shadow-[0_0_30px_rgba(59,130,246,0.5)]")
                ui.label("Network Initialization").classes("text-3xl font-bold text-white mb-2")
                ui.label("The interactive force-directed graph requires a large viewport. Collect more assets to generate links.").classes("text-slate-400 text-lg max-w-lg mb-8")
                
                ui.button("Return to Gallery", on_click=lambda: ui.navigate.to("/dam")).props("color=primary rounded outline").classes("text-white font-bold")

