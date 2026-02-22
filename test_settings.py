import asyncio
from src.core.module_loader import loader
from src.core.services.settings_service import settings_service
from src.modules.dam.settings import DAMSettings

async def test():
    loader.discover_and_load()
    loader.register_module_settings()
    # Mock settings load
    dam = settings_service.get_typed("dam", DAMSettings)
    print("DAM Settings:", dam)

if __name__ == "__main__":
    asyncio.run(test())
