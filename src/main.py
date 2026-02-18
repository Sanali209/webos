from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Depends, Request
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
import uuid
from src.core.middleware import trace_id_context
from src.core.logging import setup_logging
from src.core.database import init_db
from src.core.auth import User, auth_backend, fastapi_users
from src.core.exceptions import setup_exception_handlers
from src.core.schemas import UserRead, UserCreate, UserUpdate # I'll create these next

from src.core.module_loader import loader

# Discover Modules (Top-level for router registration)
loader.discover_and_load()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "modules" and len(sys.argv) > 2 and sys.argv[2] == "list":
        print("\n" + "="*40)
        print("WebOS - Loaded Modules")
        print("="*40)
        if not loader.loaded_modules:
            print(" No modules loaded.")
        for mod in loader.loaded_modules:
            print(f" - {mod}")
        print("="*40 + "\n")
        sys.exit(0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup Logging
    setup_logging()
    
    # Collect all models (Core + Modules)
    all_models = [User] + loader.get_all_models()
    
    # Initialize DB
    await init_db(all_models)
    
    # Auto-seed Default Admin if no users exist
    from src.core.seeding import setup_default_user
    await setup_default_user()
    
    # Trigger Startup Hooks
    loader.trigger_startup()
    
    yield
    
    # Trigger Shutdown Hooks
    loader.trigger_shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan
)

# CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Exception Handlers
setup_exception_handlers(app)

@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    token = trace_id_context.set(trace_id)
    try:
        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        return response
    finally:
        trace_id_context.reset(token)

from src.core.auth import set_task_context

# API Router
api_router = APIRouter(dependencies=[Depends(set_task_context)])

# Authentication Routers
api_router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
api_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
api_router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

from src.ui.layout import layout, ui_slots

# Module Routers (Auto-discovered)
loader.register_routes(api_router)

# Include API Router in app
app.include_router(api_router, prefix=settings.API_PREFIX)

# -----------------------------------------------------------------------------
# NiceGUI Integration
# -----------------------------------------------------------------------------
from nicegui import ui

# -----------------------------------------------------------------------------
# Storage & Caching
# -----------------------------------------------------------------------------
from src.core.storage import afs
loader.register_data_sources(afs)

# -----------------------------------------------------------------------------
# Tasks (TaskIQ)
# -----------------------------------------------------------------------------
from src.core.tasks import broker
loader.register_tasks(broker)

# Trigger UI Registration Hooks (Modules register their widgets/slots here)
loader.register_ui()

# Trigger Admin Widget Hooks
loader.register_admin_widgets()

@ui.page("/")
def index_page():
    layout()

# Mount NiceGUI to FastAPI
ui.run_with(app, title=settings.PROJECT_NAME, storage_secret=settings.SECRET_KEY)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}
