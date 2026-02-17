from typing import List, Type
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, Document
from loguru import logger

from src.core.config import settings

async def init_db(models: List[Type[Document]]):
    """
    Initialize the database connection and Beanie ODM.
    """
    logger.info(f"Connecting to MongoDB at {settings.MONGO_URL}")
    try:
        client = AsyncIOMotorClient(settings.MONGO_URL)
        await init_beanie(
            database=client[settings.MONGO_DB_NAME],
            document_models=models
        )
        logger.info("Beanie initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Beanie: {e}")
        raise
