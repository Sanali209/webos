from nicegui import ui
from src.ui.layout import MainLayout
from src.core.auth import User
from loguru import logger

@ui.page("/admin/users")
async def user_manager_page():
    with MainLayout():
        with ui.column().classes("w-full gap-4 p-4"):
            with ui.row().classes("w-full items-center gap-4"):
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/admin")).props("flat")
                ui.label("User Manager").classes("text-3xl font-black")
            
            ui.label("Manage registered users and their permissions.").classes("text-slate-500")

            # User Table
            try:
                users = await User.find_all().to_list()
                
                columns = [
                    {'name': 'email', 'label': 'Email', 'field': 'email', 'required': True, 'align': 'left', 'sortable': True},
                    {'name': 'full_name', 'label': 'Full Name', 'field': 'full_name', 'align': 'left'},
                    {'name': 'role', 'label': 'Role', 'field': 'role', 'align': 'center'},
                    {'name': 'active', 'label': 'Active', 'field': 'is_active', 'align': 'center'},
                ]
                
                rows = [
                    {
                        'email': u.email,
                        'full_name': u.full_name or "N/A",
                        'role': u.role,
                        'is_active': "✅" if u.is_active else "❌"
                    } for u in users
                ]

                ui.table(columns=columns, rows=rows, row_key='email').classes("w-full")
            
            except Exception as e:
                logger.error(f"Error loading users: {e}")
                ui.label("Failed to load users. Ensure MongoDB is running.").classes("text-red-500")

            ui.button("Create New User", icon="person_add").classes("mt-4").props("elevated")
