from nicegui import ui
import httpx

def upload_dropzone_dialog():
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-2xl p-4 gap-4"):
        with ui.row().classes("w-full items-center justify-between border-b pb-2"):
            ui.label("Upload Assets").classes("text-xl font-bold text-slate-800")
            ui.button(icon="close", on_click=dialog.close).props("flat round size=sm color=slate-400")
        
        async def handle_upload(e):
            # Read file bytes from nicegui upload event
            content = e.content.read()
            filename = e.name
            
            # Use httpx to POST to the internal API (simulating an external request)
            # Since we're inside the event loop, we can just call the service or POST to API.
            # Using API is cleaner for decoupling, but accessing the service directly is faster.
            # Let's use the API via httpx block async.
            try:
                from src.core.services.settings_service import settings_service
                token = "TODO_AUTH_TOKEN" # We would get this from session, but DAM upload API might not be authenticated strictly for local use yet.
                
                # We can also bypass httpx and call AssetService direct
                from src.core.registry import ServiceRegistry
                from src.modules.dam.services.asset_service import AssetService
                from fastapi import UploadFile
                from io import BytesIO
                
                asset_svc = ServiceRegistry.get(AssetService)
                
                # Mock FastAPI UploadFile
                upload_file = UploadFile(filename=filename, file=BytesIO(content))
                
                # Assuming user_id context is active
                from src.core.middleware import user_id_context
                uid = user_id_context.get() or "system"
                
                asset = await asset_svc.ingest(upload_file, owner_id=uid)
                ui.notify(f"Uploaded {filename} successfully!", type="positive")
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ui.notify(f"Failed to upload {filename}: {str(ex)}", type="negative")
                
        ui.upload(multiple=True, on_upload=handle_upload, auto_upload=True).classes("w-full").props("accept='image/*, video/*, audio/*, application/pdf'")
        
        with ui.row().classes("w-full justify-end mt-2"):
            ui.button("Done", on_click=dialog.close).props("color=primary")
            
    return dialog
