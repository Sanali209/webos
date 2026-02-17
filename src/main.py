from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.logging import setup_logging
from src.core.database import init_db
from src.core.auth import User, auth_backend, fastapi_users
from src.core.exceptions import setup_exception_handlers
from src.core.schemas import UserRead, UserCreate, UserUpdate # I'll create these next

from src.core.module_loader import loader

# Discover Modules (Top-level for router registration)
loader.discover_and_load()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup Logging
    setup_logging()
    
    # Collect all models (Core + Modules)
    all_models = [User] + loader.get_all_models()
    
    # Initialize DB
    await init_db(all_models)
    
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

from fastapi import APIRouter

# API Router
api_router = APIRouter()

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

# Module Routers (Auto-discovered)
loader.register_routes(api_router)

# Include API Router in app
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}
