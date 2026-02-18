from nicegui import app, ui
from src.ui.layout import MainLayout
from src.ui.registry import ui_registry, AppMetadata
from src.core.hooks import hookimpl
from .models import Secret
from beanie import PydanticObjectId
from src.core.auth import current_active_user
from loguru import logger

@ui.page("/vault")
async def vault_page():
    with MainLayout():
        ui.label("Secure Vault").classes("text-3xl font-black")
        ui.label("Your personal encrypted password manager.").classes("text-slate-500 mb-8")

        # Table of Secrets
        # OwnedDocument.find_all() automatically filters by current_user if correctly integrated in Beanies finding logic.
        # For this demo, we explicitly filter just to be sure if the global finds haven't been patched yet.
        from src.core.middleware import user_id_context
        uid = user_id_context.get()
        logger.debug(f"Vault Page - current user_id_context: {uid}")
        
        if not uid:
            # Fallback check directly in storage
            uid = app.storage.user.get("user_id")
            if uid:
                logger.debug(f"Vault Page - Fallback found uid in storage: {uid}")
                user_id_context.set(uid)
            else:
                ui.label("Please login to access your vault.").classes("text-red-500")
                ui.button("Go to Login", on_click=lambda: ui.navigate.to("/login")).classes("mt-4")
                return

        try:
            # Convert string uid to PydanticObjectId for comparison
            obj_id = PydanticObjectId(uid)
            secrets = await Secret.find(Secret.owner_id == obj_id).to_list()
        except Exception as e:
            logger.error(f"Error fetching secrets: {e}")
            secrets = []
        
        with ui.column().classes("w-full max-w-4xl gap-4"):
            with ui.row().classes("w-full justify-end"):
                ui.button("Add Secret", icon="add", on_click=lambda: add_dialog.open()).props("elevated")

            if not secrets:
                ui.label("No secrets stored yet.").classes("italic text-slate-400 mt-4")
            
            with ui.grid(columns=1).classes("w-full gap-2"):
                for secret in secrets:
                    with ui.card().classes("w-full p-4 hover:shadow-md transition-shadow"):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.column():
                                ui.label(secret.label).classes("font-bold text-lg")
                                ui.label(f"User: {secret.username}").classes("text-sm text-slate-500")
                            
                            with ui.row().classes("gap-2"):
                                # Secret toggles
                                pwd_label = ui.label("********").classes("font-mono font-bold text-slate-400")
                                def toggle(l=pwd_label, s=secret):
                                    if l.text == "********":
                                        l.set_text(s.password)
                                        l.classes(replace="text-red-600")
                                    else:
                                        l.set_text("********")
                                        l.classes(replace="text-slate-400")
                                
                                ui.button(icon="visibility", on_click=toggle).props("flat dense")
                                ui.button(icon="delete", color="red", on_click=lambda s=secret: s.delete()).props("flat dense")

        # Add Dialog
        with ui.dialog() as add_dialog, ui.card().classes("p-6 gap-4"):
            ui.label("New Secret").classes("text-xl font-bold")
            label_in = ui.input("Label (e.g. Gmail)")
            user_in = ui.input("Username")
            pass_in = ui.input("Password", password=True)
            
            async def save():
                try:
                    obj_id = PydanticObjectId(uid)
                    s = Secret(
                        label=label_in.value,
                        username=user_in.value,
                        password=pass_in.value,
                        owner_id=obj_id,
                        created_by=obj_id,
                        updated_by=obj_id
                    )
                    await s.insert()
                    ui.notify("Secret saved!")
                    add_dialog.close()
                    ui.navigate.to("/vault") # Refresh
                except Exception as e:
                    logger.error(f"Error saving secret: {e}")
                    ui.notify(f"Error: {e}", type="negative")
                
            ui.button("Save", on_click=save).classes("w-full")

@hookimpl
def register_ui():
    """Register the Vault App."""
    ui_registry.register_app(AppMetadata(
        name="Vault",
        icon="security",
        route="/vault",
        description="Securely store your passwords with user isolation.",
        commands=["save password", "my secrets", "credentials"]
    ))
toxicology_report = "Vault Module initialized"
