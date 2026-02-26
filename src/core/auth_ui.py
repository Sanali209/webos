from functools import wraps
from nicegui import ui, app
from loguru import logger
from src.core.auth import current_active_user

def login_required(func):
    """
    Decorator for NiceGUI page functions.
    Redirects to /login if the user is not authenticated in the session.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 1. Check NiceGUI session storage
        # The user_id is typically set during the login flow in app.storage.user
        user_id = app.storage.user.get("user_id")

        if not user_id:
            logger.warning(f"Access denied to {func.__name__}: No user_id in session.")
            ui.navigate.to("/login")
            return

        # 2. (Optional) Verify against DB if needed, but session check is usually sufficient for UI routing
        # We can also populate user_id_context here if not already done by middleware
        from src.core.middleware import user_id_context
        if not user_id_context.get():
            user_id_context.set(user_id)

        return await func(*args, **kwargs)
    return wrapper
