from nicegui import app, ui
from src.core.hooks import hookimpl
from src.ui.registry import ui_registry, AppMetadata
from src.core.auth import get_user_manager, auth_backend, User
from src.core.middleware import user_id_context
import httpx
from src.core.config import settings
from . import debug  # Load debug page

@ui.page("/login")
def login_page():
    from src.ui.layout import MainLayout
    
    with MainLayout():
        with ui.card().classes("w-full max-w-md mx-auto p-8 gap-6 shadow-xl rounded-2xl mt-12"):
            with ui.column().classes("items-center w-full gap-2"):
                ui.icon("lock").classes("text-5xl text-primary mb-2")
                ui.label("Secure Login").classes("text-2xl font-black text-slate-800")
                ui.label("Enter your credentials to access WebOS.").classes("text-slate-400 text-sm text-center")

            username = ui.input("Email").classes("w-full").props("outlined")
            password = ui.input("Password", password=True).classes("w-full").props("outlined")
            
            async def try_login():
                try:
                    # We can call the FastAPI router directly for auth
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"http://localhost:8000{settings.API_PREFIX}/auth/jwt/login",
                            data={
                                "username": username.value,
                                "password": password.value,
                            }
                        )
                        
                    if response.status_code == 200:
                        token = response.json().get("access_token")
                        
                        # Fetch user details to get ID
                        async with httpx.AsyncClient() as client:
                            user_response = await client.get(
                                f"http://localhost:8000{settings.API_PREFIX}/users/me",
                                headers={"Authorization": f"Bearer {token}"}
                            )
                        
                        if user_response.status_code == 200:
                            user_data = user_response.json()
                            uid = str(user_data["id"])
                            app.storage.user["user_id"] = uid
                            user_id_context.set(uid) # Set immediately for the current page
                            ui.notify(f"Welcome back, {user_data.get('email')}!", type="positive")
                            ui.navigate.to("/")
                        else:
                            ui.notify("Failed to fetch user profile.", type="negative")
                    else:
                        ui.notify("Invalid credentials.", type="negative")
                except Exception as e:
                    ui.notify(f"Login error: {e}", type="negative")

            ui.button("Sign In", on_click=try_login).classes("w-full py-4 rounded-xl text-lg font-bold").props("elevated")
            
            with ui.row().classes("w-full justify-center mt-4 text-xs text-slate-400 gap-1"):
                ui.label("Forgot Password?")
                ui.label("|")
                ui.label("Create Account")

# @hookimpl
# def register_ui():
#     """Register the Auth module."""
#     ui_registry.register_app(AppMetadata(
#         name="Login",
#         icon="login",
#         route="/login",
#         description="Authenticate to access protected system modules.",
#         category="System",
#         is_system=True
#     ))

toxicology_report = "Auth UI Module Initialized"
