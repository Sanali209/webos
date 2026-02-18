from taskiq_redis import RedisAsyncResultBackend, ListQueueBroker
from taskiq import TaskiqEvents
from src.core.config import settings
from loguru import logger

from .middleware import ContextPropagationMiddleware

# Configuration for Redis broker
broker = ListQueueBroker(
    url=settings.REDIS_URL,
).with_result_backend(
    RedisAsyncResultBackend(redis_url=settings.REDIS_URL),
).with_middlewares(
    ContextPropagationMiddleware(),
)

@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state):
    """Worker startup logic."""
    logger.info("TaskIQ Worker starting up...")
    # Here we could initialize DB connections if tasks need them
    from src.core.database import init_db
    from src.core.module_loader import loader
    from src.core.auth import User
    
    loader.discover_and_load()
    all_models = [User] + loader.get_all_models()
    await init_db(all_models)
    logger.info("Worker DB connection initialized.")

@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state):
    """Worker shutdown logic."""
    logger.info("TaskIQ Worker shutting down...")
