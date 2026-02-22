from nicegui import ui
from src.ui.page_slot_registry import page_slot_registry
from src.ui.layout import MainLayout

page_slot_registry.declare("/dam/assets/{id}", "details_panel", "Right sidebar details panel for an asset")
page_slot_registry.declare("/dam/assets/{id}", "actions_toolbar", "Top actions toolbar for an asset")

@ui.page('/dam/assets/{id}')
def viewer_page(id: str):
    """Asset viewer with two-panel layout: Preview and Details Tabs."""
    with MainLayout() as l:
        container = ui.row().classes("w-full h-[calc(100vh-120px)] flex-nowrap gap-6")
        
        async def load_asset():
            from beanie import PydanticObjectId
            from src.modules.dam.models import Asset
            
            try:
                asset = await Asset.get(PydanticObjectId(id))
            except Exception:
                asset = None
                
            with container:
                if not asset:
                    ui.label("Asset not found.").classes("text-2xl font-black text-slate-300 m-auto uppercase tracking-widest")
                    return
                
                # Left Panel - Preview
                with ui.column().classes("flex-grow min-w-0 h-full bg-slate-100 rounded-3xl border border-slate-200 overflow-hidden relative items-center justify-center p-4"):
                    if asset.primary_type in ["image"]:
                        img_url = f"/api/dam/assets/{asset.id}/download"
                        ui.image(img_url).classes("max-w-full max-h-full object-contain rounded-xl shadow-sm")
                    elif asset.primary_type in ["video"]:
                        vid_url = f"/api/dam/assets/{asset.id}/download"
                        ui.video(vid_url, autoplay=False, loop=False, muted=False).classes("max-w-full max-h-full rounded-xl shadow-sm")
                    else:
                        ui.icon("insert_drive_file").classes("text-[12rem] text-slate-300")
                        ui.label(asset.filename).classes("mt-6 font-bold text-slate-500 text-lg")

                # Right Panel - Details & Tabs
                with ui.column().classes("w-96 shrink-0 h-full bg-white rounded-3xl border border-slate-200 p-0 overflow-hidden flex flex-col shadow-sm"):
                    
                    # 1. Header Area
                    with ui.column().classes("w-full p-6 border-b border-slate-100 bg-slate-50 gap-2 shrink-0"):
                        ui.label(asset.filename).classes("font-black text-slate-800 text-xl break-all leading-tight")
                        with ui.row().classes("w-full items-center justify-between text-xs font-bold text-slate-400 uppercase tracking-wider"):
                            ui.label(asset.primary_type)
                            if asset.size:
                                ui.label(f"{asset.size / 1024 / 1024:.2f} MB")
                            ui.label(asset.created_at.strftime("%b %d, %Y") if getattr(asset, 'created_at', None) else "Unknown")
                            
                        # Actions
                        with ui.row().classes("w-full mt-4 gap-2"):
                            ui.button("Download", on_click=lambda: ui.download(f"/api/dam/assets/{asset.id}/download", asset.filename)).props("unelevated outline color=primary").classes("flex-grow rounded-xl font-bold")
                            # Render hooks from other modules (e.g. BlogPost linker)
                            page_slot_registry.render("/dam/assets/{id}", "actions_toolbar", asset=asset)

                    # 2. Tabs Shell
                    with ui.tabs().classes("w-full text-slate-500 font-bold text-sm") as tabs:
                        tab_info = ui.tab("INFO")
                        tab_ai = ui.tab("AI")
                        tab_links = ui.tab("LINKS")
                    
                    # 3. Tab Panels
                    with ui.tab_panels(tabs, value=tab_info).classes("w-full flex-grow p-0 bg-transparent overflow-y-auto"):
                        
                        # INFO TAB
                        with ui.tab_panel(tab_info).classes("p-6 gap-6 flex flex-col w-full min-h-full"):
                            ui.label("METADATA").classes("text-[10px] font-black text-slate-400 uppercase tracking-widest")
                            ui.input("Title", value=asset.title or "").classes("w-full").props("outlined dense bg-white")
                            ui.textarea("Description", value=asset.description or "").classes("w-full").props("outlined bg-white")
                            
                            if asset.metadata:
                                ui.label("EXTRACTED (EXIF/PROBE)").classes("text-[10px] font-black text-slate-400 uppercase tracking-widest mt-4")
                                with ui.column().classes("w-full gap-0 bg-slate-50 rounded-xl p-4 border border-slate-100"):
                                    for k, v in asset.metadata.items():
                                        if isinstance(v, dict): continue
                                        with ui.row().classes("w-full justify-between items-center py-1.5 border-b border-white last:border-0"):
                                            ui.label(str(k)).classes("text-[10px] font-black text-slate-400 uppercase tracking-wider")
                                            ui.label(str(v)).classes("text-sm text-slate-700 font-medium text-right max-w-[200px] truncate").tooltip(str(v))
                                        
                            # Render hooks for external information (e.g., Blog Posts using this asset)
                            page_slot_registry.render("/dam/assets/{id}", "details_panel", asset=asset)
                            
                        # AI TAB
                        with ui.tab_panel(tab_ai).classes("p-6 gap-6 flex flex-col w-full min-h-full"):
                            if asset.ai_caption:
                                ui.label("AI CAPTION").classes("text-[10px] font-black text-slate-400 uppercase tracking-widest")
                                ui.label(asset.ai_caption).classes("text-sm italic text-slate-700 bg-blue-50 p-4 rounded-xl border border-blue-100 leading-relaxed shadow-inner")
                            
                            if asset.ai_tags:
                                ui.label("SEMANTIC TAGS").classes("text-[10px] font-black text-slate-400 uppercase tracking-widest mt-2")
                                with ui.row().classes("gap-2"):
                                    for tag in asset.ai_tags:
                                        conf = getattr(asset, 'ai_confidence', {}).get(tag, 1.0)
                                        bg = "bg-green-100 text-green-800 border-green-200" if conf > 0.8 else "bg-slate-100 text-slate-700 border-slate-200"
                                        ui.label(f"{tag} ({conf:.2f})").classes(f"text-[10px] font-bold px-3 py-1.5 rounded-full border {bg}")
                                        
                            if asset.detected_objects:
                                ui.label("DETECTED OBJECTS").classes("text-[10px] font-black text-slate-400 uppercase tracking-widest mt-2")
                                with ui.column().classes("w-full gap-0 bg-slate-50 rounded-xl border border-slate-100 overflow-hidden"):
                                    for obj in asset.detected_objects:
                                        with ui.row().classes("w-full justify-between items-center p-3 border-b border-white last:border-0 hover:bg-slate-100"):
                                            ui.label(obj.class_name).classes("text-sm font-bold text-slate-700 capitalize")
                                            ui.label(f"{obj.confidence*100:.0f}%").classes("text-xs font-black text-slate-400 bg-white px-2 py-0.5 rounded shadow-sm")

                        # LINKS TAB
                        with ui.tab_panel(tab_links).classes("p-6 gap-4 flex flex-col w-full min-h-full"):
                            ui.label("RELATIONSHIPS").classes("text-[10px] font-black text-slate-400 uppercase tracking-widest")
                            
                            links_container = ui.column().classes("w-full gap-3")
                            
                            async def load_links():
                                from src.modules.dam.models import Link
                                links = await Link.find(
                                    {"$or": [{"source_id": asset.id}, {"target_id": asset.id}]}
                                ).to_list()
                                
                                if not links:
                                    with links_container:
                                        ui.label("No relationships found.").classes("text-sm text-slate-400 italic p-4 text-center w-full bg-slate-50 rounded-xl border border-dashed border-slate-200")
                                    return
                                    
                                with links_container:
                                    for link in links:
                                        is_source = link.source_id == asset.id
                                        other_id = link.target_id if is_source else link.source_id
                                        
                                        with ui.card().classes("w-full p-4 bg-white shadow-sm border border-slate-200 rounded-xl hover:border-slate-300 transition-colors"):
                                            with ui.row().classes("w-full justify-between items-center mb-2"):
                                                ui.label(link.relation).classes("text-[10px] font-black text-slate-500 uppercase bg-slate-100 px-2 py-1 rounded")
                                                ui.label(f"{link.weight:.2f} score").classes("text-[10px] font-black text-blue-400 bg-blue-50 px-2 py-1 rounded")
                                            with ui.row().classes("w-full items-center"):
                                                ui.icon("arrow_forward" if is_source else "arrow_back").classes("text-slate-400 text-sm mr-2")
                                                ui.link(f"Asset {str(other_id)[-6:]}", f"/dam/assets/{other_id}").classes("text-sm font-bold text-primary no-underline hover:underline")
                                                
                            ui.timer(0.1, load_links, once=True)
                            
                            ui.space()
                            ui.button("Open Graph Explorer", on_click=lambda: ui.navigate.to("/dam/graph"), icon="hub").props("flat color=primary").classes("w-full mt-4 bg-slate-50 font-bold")
        
        ui.timer(0.1, load_asset, once=True)

