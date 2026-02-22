from nicegui import ui
from src.ui.layout import MainLayout
from src.core.registry import ServiceRegistry
from src.modules.dam.services.unified_search import UnifiedSearchService
from src.modules.dam.schemas.search import SearchRequest, AssetFilter
from src.modules.dam.models import Asset
from src.core.services.settings_service import settings_service
from src.modules.dam.settings import DAMSettings
from src.modules.dam.services.watcher_service import WatcherService
from src.ui.components.folder_picker import FolderPicker
from pathlib import Path

@ui.page('/dam')
def gallery_page():
    with MainLayout():
        with ui.row().classes("w-full h-full min-h-[calc(100vh-80px)] flex-nowrap gap-4"):
            
            # Sidebar for Facets
            with ui.column().classes("w-60 shrink-0 bg-slate-50 border border-slate-200 rounded-xl p-3 gap-3 hidden md:flex h-max"):
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
                with ui.row().classes("w-full items-center gap-3 mb-3 bg-white p-2 rounded-xl border border-slate-200 shadow-sm"):
                    ui.icon("search").classes("text-slate-400 text-xl ml-2")
                    search_input = ui.input(placeholder="Search by keywords, tags, or concepts...").props("borderless standout=bg-transparent").classes("flex-grow text-lg")
                    search_btn = ui.button("Search", on_click=lambda: load_assets()).props("color=primary rounded").classes("font-bold px-6")
                    
                    # Watch Folders Dialog Builder
                    with ui.dialog() as watch_dialog, ui.card().classes("w-full max-w-lg p-0"):
                        with ui.row().classes("w-full bg-primary text-white p-4 items-center"):
                            ui.icon("folder_special", size="sm")
                            ui.label("Manage Watch Folders").classes("text-lg font-bold flex-grow")
                            ui.button(icon="close", on_click=watch_dialog.close).props("flat color=white")
                        
                        watch_dialog_content = ui.column().classes("w-full p-4 gap-2 bg-slate-50")
                        
                        async def handle_folder_picked(new_path: str):
                            settings = settings_service.get_typed("dam", DAMSettings)
                            if new_path not in settings.watch_paths:
                                settings.watch_paths.append(new_path)
                                await _save_and_apply(settings)
                        
                        def picker_trigger():
                            FolderPicker(callback=handle_folder_picked).open()

                        async def _save_and_apply(settings: DAMSettings):
                            try:
                                await settings_service.update("dam", settings.model_dump())
                                watcher = ServiceRegistry.get(WatcherService)
                                
                                physical_paths = []
                                for p in settings.watch_paths:
                                    if p.startswith("fs://local/"):
                                        # strip fs://local/ to get physical path for watchdog
                                        physical_paths.append(Path(p[11:]))
                                    elif p.startswith("fs://"):
                                        # watchdog won't support non-local correctly, but fallback
                                        ui.notify(f"Watchdog may not support non-local path: {p}", type="warning")
                                        physical_paths.append(Path(p))
                                    else:
                                        physical_paths.append(Path(p))
                                        
                                await watcher.reload_watches(physical_paths)
                                ui.notify("Watch folders updated", type="positive")
                                watch_dialog.close()
                                open_watch_dialog()
                            except Exception as e:
                                ui.notify(f"Failed to update watcher: {e}", type="negative")
                            
                        async def remove_path(idx: int):
                            settings = settings_service.get_typed("dam", DAMSettings)
                            settings.watch_paths.pop(idx)
                            await _save_and_apply(settings)
                            
                        def open_watch_dialog():
                            watch_dialog_content.clear()
                            settings = settings_service.get_typed("dam", DAMSettings)
                            with watch_dialog_content:
                                if not settings.watch_paths:
                                    ui.label("No watch folders configured.").classes("italic text-slate-500 w-full text-center p-4")
                                else:
                                    for idx, p in enumerate(settings.watch_paths):
                                        with ui.row().classes("w-full items-center justify-between border-b border-slate-200 pb-2"):
                                            ui.icon("folder").classes("text-slate-400")
                                            ui.label(p).classes("font-mono text-sm flex-grow word-break-all ml-2 text-slate-700")
                                            ui.button(icon="delete", on_click=lambda i=idx: remove_path(i)).props("flat color=red dense")
                                
                                ui.button("Add Folder", icon="add", on_click=picker_trigger).props("outline color=primary w-full").classes("mt-4")
                            watch_dialog.open()

                    # Settings Button
                    ui.button(icon="settings", on_click=open_watch_dialog).props("outline color=slate rounded").classes("ml-1").tooltip("Watch Folders")
                
                grid_container = ui.grid(columns=5).classes("w-full gap-3 pb-20")
                
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
