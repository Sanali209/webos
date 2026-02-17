import asyncio
from src.core.kernel import Engine
from src.core.module import BaseModule
from src.core.hooks import hookimpl
from loguru import logger

class HelloModule(BaseModule):
    """A minimal module to demonstrate the kernel boot sequence."""
    name: str = "hello_kernel"
    version: str = "1.0.0"

    async def initialize(self) -> None:
        logger.info("HelloModule: Initializing...")

    @hookimpl
    async def post_setup(self) -> None:
        logger.info("HelloModule: Kernel setup is complete!")

    async def shutdown(self) -> None:
        logger.info("HelloModule: Shutting down safely.")

async def run_sample():
    # 1. Initialize Engine
    logger.info("--- Starting Hello Kernel Sample ---")
    engine = Engine()
    
    # 2. Register our module manually (instead of discovery for this simple sample if we want)
    # But usually we want to show discovery. 
    # For this sample, we'll just let discovery find it if it's in src.modules
    # Or we can register it manually as a plugin:
    hello = HelloModule()
    engine._modules[hello.name] = hello
    engine.pm.register(hello)
    
    # 3. Start Engine
    await engine.start()
    
    # 4. Wait a moment
    await asyncio.sleep(1)
    
    # 5. Stop Engine
    await engine.stop()
    logger.info("--- Sample Finished ---")

if __name__ == "__main__":
    asyncio.run(run_sample())
