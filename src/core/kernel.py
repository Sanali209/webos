import importlib
import inspect
import pkgutil
import threading
from typing import Dict, List, Optional, Type

from loguru import logger
from src.core.di import DIContainer, container
from src.core.exceptions import KernelError, ModuleLoadError
from src.core.hooks import get_plugin_manager
from src.core.infrastructure.persistence.beanie_adapter import DatabaseManager
from src.core.module import IModule

class Engine:
    def __init__(self, di_container: DIContainer = container):
        self._di = di_container
        self._modules: Dict[str, IModule] = {}
        self.pm = get_plugin_manager()
        self._lock = threading.RLock()
        
        # Core Infrastructure
        self.db = DatabaseManager(
            mongodb_url="mongodb://localhost:27017", 
            db_name="webos_engine"
        )
        self._di.register(DatabaseManager, instance=self.db)
        self._is_running = False

    def discover_modules(self, package_path: str = "src.modules"):
        """Dynamically discovers and registers modules from the specified package."""
        logger.info(f"Discovering modules in {package_path}...")
        try:
            package = importlib.import_module(package_path)
        except ImportError as e:
            logger.error(f"Failed to import module package {package_path}: {e}")
            return

        for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package_path + "."):
            if is_pkg:
                self._load_module(name)

    def _load_module(self, module_name: str):
        """Loads a single module from its package name."""
        logger.debug(f"Loading module: {module_name}")
        try:
            mod = importlib.import_module(module_name)
            
            # Look for a class that implements IModule
            module_class: Optional[Type[IModule]] = None
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if isinstance(attr, type) and issubclass(attr, IModule) and attr is not IModule:
                    module_class = attr
                    break

            if not module_class:
                logger.warning(f"No IModule implementation found in {module_name}")
                return

            # Resolve/Create instance via DI
            instance = self._di.resolve(module_class)
            self._modules[instance.name] = instance
            
            # Register as a plugin for hooks
            self.pm.register(instance)
            logger.info(f"Module {instance.name} (v{instance.version}) loaded successfully.")

        except Exception as e:
            logger.exception(f"Failed to load module {module_name}: {e}")
            # In Phase 5 we will add a "Faulty Module" registry here

    async def start(self):
        """Orchestrates the engine boot sequence."""
        if self._is_running:
            return

        logger.info("Starting Web OS Engine boot sequence...")
        with self._lock:
            self._is_running = True

        # 1. Module Discovery
        self.discover_modules()

        # 2. Database Initialization (if models registered)
        if self.db.doc_models:
            await self.db.initialize()

        # 2. Module Initialization (Ordered)
        for module in self._modules.values():
            try:
                logger.debug(f"Initializing module: {module.name}")
                await module.initialize()
                results = self.pm.hook.on_module_load(module=module)
                for res in results:
                    if inspect.isawaitable(res):
                        await res
            except Exception as e:
                logger.error(f"Error during initialization of {module.name}: {e}")
                raise ModuleLoadError(f"Module {module.name} failed to initialize.", details={"error": str(e)})

        # 3. Post Setup Hooks
        results = self.pm.hook.post_setup()
        for res in results:
            if inspect.isawaitable(res):
                await res
        
        # 5. Mount UI (Synchronous)
        self.pm.hook.mount_ui()

        logger.info("Web OS Engine started successfully.")

    async def stop(self):
        """Orchestrates the engine shutdown sequence."""
        logger.info("Shutting down Web OS Engine...")
        for module in reversed(list(self._modules.values())):
            try:
                await module.shutdown()
            except Exception as e:
                logger.error(f"Error during shutdown of {module.name}: {e}")
        
        with self._lock:
            self._is_running = False
        logger.info("Web OS Engine stopped.")
