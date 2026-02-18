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
        # Collect all models (Core + Modules)
        all_models = [User] + loader.get_all_models()
        print(f"Discovered {len(all_models)} models.")
        
        # Trigger UI Hooks
        print("Triggering UI Hooks...")
        loader.register_ui()
        
        # Check slots & registry
        from src.ui.layout import ui_slots
        from src.ui.registry import ui_registry
        print(f"Sidebar slots: {len(ui_slots._slots['sidebar'])}")
        print(f"Dashboard slots: {len(ui_slots._slots['dashboard_widgets'])}")
        print(f"Registered apps: {len(ui_registry.apps)}")
        for app in ui_registry.apps:
            print(f" - {app.name} ({app.route})")
        
        # Initialize DB (Optional for loading test)
        logger.info("Initializing DB...")
        await init_db(all_models)
        logger.success("Beanie initialized successfully with all models")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_load())
