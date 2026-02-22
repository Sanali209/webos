from nicegui import ui
from src.ui.layout import MainLayout
from src.core.registry import ServiceRegistry
from src.modules.dam.services.unified_search import UnifiedSearchService
from src.modules.dam.schemas.search import SearchRequest, AssetFilter
from src.modules.dam.models import Asset

@ui.page('/dam')
def gallery_page():
    with MainLayout():
        with ui.row().classes("w-full h-full min-h-[calc(100vh-120px)] flex-nowrap gap-6"):
            
            # Sidebar for Facets
            with ui.column().classes("w-64 shrink-0 bg-slate-50 border border-slate-200 rounded-2xl p-4 gap-4 hidden md:flex h-max"):
                ui.label("FILTERS").classes("text-[10px] font-black text-slate-400 uppercase tracking-widest")
                
                type_filter = ui.select(
                    ["image", "video", "audio", "document"], 
                    label="Media Type", 
                    multiple=True,
                    clearable=True
                ).classes("w-full").props("options-dense outlined bg-white")
                
                status_filter = ui.select(
                    ["ready", "processing", "error", "missing"],
                    label="Status",
                    multiple=True,
                    clearable=True
                ).classes("w-full").props("options-dense outlined bg-white")
                
                tags_filter = ui.input("Tags (comma separated)").classes("w-full").props("outlined bg-white placeholder-slate-400")
                
                ui.button("Apply Filters", on_click=lambda: load_assets()).props("color=primary outline").classes("w-full mt-2")
            
            # Main Gallery Area
            with ui.column().classes("flex-grow min-w-0 h-full"):
                with ui.row().classes("w-full items-center gap-4 mb-4 bg-white p-2 rounded-2xl border border-slate-200 shadow-sm"):
                    ui.icon("search").classes("text-slate-400 text-xl ml-2")
                    search_input = ui.input(placeholder="Search by keywords, tags, or concepts...").props("borderless standout=bg-transparent").classes("flex-grow text-lg")
                    search_btn = ui.button("Search", on_click=lambda: load_assets()).props("color=primary rounded").classes("font-bold px-6")
                
                grid_container = ui.grid(columns=4).classes("w-full gap-4 pb-20")
                
                async def load_assets():
                    grid_container.clear()
                    
                    try:
                        search_svc = ServiceRegistry.get(UnifiedSearchService)
                    except ValueError:
                        with grid_container:
                            ui.label("Search service initializing... Please refresh.").classes("col-span-4 text-slate-400 italic text-center p-8")
                        return
                        
                    # Build filter
                    af = AssetFilter()
                    if type_filter.value: af.asset_types = type_filter.value
                    if status_filter.value: af.status = status_filter.value
                    if tags_filter.value: af.tags = [t.strip() for t in tags_filter.value.split(",") if t.strip()]
                    
                    req = SearchRequest(
                        query=search_input.value if search_input.value else None,
                        filter=af,
                        limit=48
                    )
                    
                    try:
                        page = await search_svc.search(req)
                        
                        if not page.items:
                            with grid_container:
                                ui.label("No assets found.").classes("text-slate-400 font-bold col-span-4 text-center p-12 text-xl")
                            return
                            
                        # Fetch actual assets
                        asset_ids = [hit.asset_id for hit in page.items]
                        from beanie import PydanticObjectId
                        assets = await Asset.find({"_id": {"$in": [PydanticObjectId(aid) for aid in asset_ids]}}).to_list()
                        asset_map = {str(a.id): a for a in assets}
                        
                        for hit in page.items:
                            asset = asset_map.get(hit.asset_id)
                            if not asset: continue
                            
                            with grid_container:
                                with ui.card().classes("p-0 cursor-pointer overflow-hidden group hover:shadow-xl transition-all duration-300 border border-slate-200 aspect-square relative"):
                                    img_url = f"/api/dam/assets/{asset.id}/thumbnail/small"
                                    
                                    if asset.primary_type in ["image", "video"]:
                                        ui.image(img_url).classes("w-full h-full object-cover group-hover:scale-110 transition-transform duration-700")
                                    else:
                                        with ui.column().classes("w-full h-full bg-slate-50 items-center justify-center"):
                                            ui.icon("description").classes("text-6xl text-slate-300")
                                            
                                    with ui.column().classes("p-3 w-full bg-white/95 backdrop-blur absolute bottom-0 translate-y-full group-hover:translate-y-0 transition-transform duration-300"):
                                        ui.label(asset.filename).classes("font-bold text-xs truncate w-full text-slate-800").tooltip(asset.filename)
                                        if getattr(asset, 'ai_caption', None):
                                            ui.label(asset.ai_caption).classes("text-[10px] text-slate-500 line-clamp-2 mt-1 leading-tight")
                                            
                                    # Invisible button overlay for click routing
                                    ui.button(on_click=lambda a=asset.id: ui.navigate.to(f"/dam/assets/{a}")).classes("absolute inset-0 opacity-0 w-full h-full")
                                    
                                    # Status badges
                                    if asset.status == "processing":
                                        with ui.row().classes("absolute top-2 left-2 bg-yellow-500 text-white text-[9px] font-black px-1.5 py-0.5 rounded shadow"):
                                            ui.label("PROCESSING")
                                            
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        with grid_container:
                            ui.label(f"Search error: {e}").classes("text-red-500 col-span-4 p-4 bg-red-50 rounded")

                search_input.on('keydown.enter', load_assets)
                
                # Load initially
                ui.timer(0.1, load_assets, once=True)
