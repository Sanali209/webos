from src.core.module import BaseModule
from loguru import logger

class DemoModule(BaseModule):
    name: str = "demo"
    version: str = "1.0.0"

    def __init__(self):
        self.initialized = False
        self.shutdown_done = False

    async def initialize(self) -> None:
        logger.info("DemoModule initializing...")
        self.initialized = True

    async def shutdown(self) -> None:
        logger.info("DemoModule shutting down...")
        self.shutdown_done = True
