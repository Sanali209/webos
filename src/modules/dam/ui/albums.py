from nicegui import ui
from src.ui.layout import MainLayout

@ui.page('/dam/albums')
def albums_list_page():
    with MainLayout():
        with ui.row().classes("w-full items-center justify-between mb-8"):
            with ui.column().classes("gap-1"):
                ui.label('Albums').classes("text-3xl font-black text-slate-800 tracking-tight")
                ui.label('Organize your selected media assets into persistent collections.').classes("text-slate-400 font-medium")
            ui.button("New Album", icon="add").props("color=primary rounded").classes("font-bold px-6")
            
        container = ui.grid(columns=4).classes("w-full gap-6")
        
        async def load_albums():
            from src.modules.dam.models import Album
            albums = await Album.find_all().to_list()
            
            with container:
                if not albums:
                    ui.label("No albums found.").classes("text-slate-400 italic col-span-4 p-12 text-center w-full border-2 border-dashed border-slate-200 rounded-2xl")
                    return
                    
                for a in albums:
                    with ui.card().classes("w-full p-6 hover:shadow-xl transition-all duration-300 border border-slate-200 cursor-pointer rounded-2xl bg-white hover:-translate-y-1 relative group"):
                        with ui.row().classes("w-full items-start justify-between mb-4"):
                            ui.icon("collections", color="primary", size="2rem").classes("bg-blue-50 p-3 rounded-2xl text-blue-500")
                            ui.label(f"{len(a.assets)} items").classes("text-[10px] font-black text-slate-400 bg-slate-100 px-2 py-1 rounded")
                            
                        ui.label(a.name).classes("font-black text-slate-800 text-lg w-full truncate")
                        ui.label(a.description or "No description").classes("text-xs text-slate-500 line-clamp-2 mt-1 h-8")
                        
                        ui.button(on_click=lambda id=a.id: ui.navigate.to(f"/dam/albums/{id}")).classes("absolute inset-0 opacity-0 w-full h-full")
                        
        ui.timer(0.1, load_albums, once=True)

@ui.page('/dam/albums/{id}')
def albums_detail_page(id: str):
    with MainLayout():
        container = ui.column().classes("w-full gap-6")
        
        async def load_album():
            from beanie import PydanticObjectId
            from src.modules.dam.models import Album, Asset
            
            try:
                album = await Album.get(PydanticObjectId(id))
            except Exception:
                album = None
                
            with container:
                if not album:
                    ui.label("Album not found").classes("text-2xl text-slate-400 font-bold")
                    return
                    
                with ui.row().classes("w-full items-center justify-between border-b border-slate-200 pb-6"):
                    with ui.column().classes("gap-1"):
                        with ui.row().classes("items-center gap-2 text-slate-400 text-sm font-bold tracking-widest uppercase mb-2 hover:text-primary cursor-pointer").on("click", lambda: ui.navigate.to("/dam/albums")):
                            ui.icon("arrow_back")
                            ui.label("All Albums")
                            
                        ui.label(album.name).classes("text-4xl font-black text-slate-800 tracking-tight")
                        ui.label(album.description).classes("text-slate-500 font-medium text-lg")
                        
                grid_container = ui.grid(columns=4).classes("w-full gap-4 mt-4")
                
                with grid_container:
                    if not album.assets:
                        ui.label("Empty album").classes("text-slate-400 italic text-center p-12 col-span-4 w-full border-2 border-dashed border-slate-200 rounded-2xl")
                        return
                        
                    assets = await Asset.find({"_id": {"$in": album.assets}}).to_list()
                    for asset in assets:
                         with ui.card().classes("p-0 cursor-pointer overflow-hidden group hover:shadow-xl transition-all duration-300 border border-slate-200 aspect-square relative"):
                             img_url = f"/api/dam/assets/{asset.id}/thumbnail/small"
                             ui.image(img_url).classes("w-full h-full object-cover group-hover:scale-110 transition-transform duration-700")
                             with ui.column().classes("p-3 w-full bg-white/95 backdrop-blur absolute bottom-0 translate-y-full group-hover:translate-y-0 transition-transform duration-300"):
                                 ui.label(asset.filename).classes("font-bold text-xs truncate w-full")
                             ui.button(on_click=lambda a=asset.id: ui.navigate.to(f"/dam/assets/{a}")).classes("absolute inset-0 opacity-0 w-full h-full")
                             
        ui.timer(0.1, load_album, once=True)
