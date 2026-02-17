import asyncio
from src.core.module_loader import loader
from src.core.database import init_db
from src.core.auth import User
from loguru import logger

async def test_load():
    try:
        logger.info("Importing src.main.app...")
        from src.main import app
        logger.success("App imported successfully")
        
        logger.info(f"Loaded modules: {loader.loaded_modules}")
        
        models = [User] + loader.get_all_models()
        logger.info(f"Collected models: {models}")
        
        logger.info("Initializing DB...")
        await init_db(models)
        logger.success("Beanie initialized successfully with all models")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_load())
