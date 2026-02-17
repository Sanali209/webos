import importlib
import pkgutil
from pathlib import Path
from typing import List, Type, Dict, Any

import pluggy
from beanie import Document
from fastapi import FastAPI
from loguru import logger

from src.core.hooks import WebOSHookSpec, hookimpl

class AutoDiscoveryHooks:
    """
    Hook implementation that follows naming conventions to discover models and routers.
    """
    def __init__(self, module_name: str):
        self.module_name = module_name

    @hookimpl
    def register_models(self) -> List[Type[Document]]:
        try:
            models_mod = importlib.import_module(f"{self.module_name}.models")
            models = []
            for attr_name in dir(models_mod):
                attr = getattr(models_mod, attr_name)
                if isinstance(attr, type) and issubclass(attr, Document) and attr is not Document:
                    models.append(attr)
            logger.debug(f"Auto-discovered {len(models)} models in {self.module_name}")
            return models
        except ImportError as e:
            if f"{self.module_name}.models" not in str(e):
                logger.error(f"Error importing models for {self.module_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error discovering models for {self.module_name}: {e}")
            return []

    @hookimpl
    def register_routes(self, app: FastAPI):
        logger.debug(f"Executing register_routes for {self.module_name}")
        try:
            router_mod = importlib.import_module(f"{self.module_name}.router")
            if hasattr(router_mod, "router"):
                app.include_router(router_mod.router)
                logger.info(f"Auto-registered router for {self.module_name} at {router_mod.router.prefix}")
            else:
                logger.warning(f"Module {self.module_name}.router has no 'router' attribute")
        except ImportError as e:
            if f"{self.module_name}.router" not in str(e):
                logger.error(f"Error importing router for {self.module_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error registering routes for {self.module_name}: {e}")

class ModuleLoader:
    """
    Handles discovery and loading of WebOS modules.
    Supports auto-discovery of models.py and router.py.
    """

    def __init__(self, modules_path: str = "src.modules"):
        self.modules_path = modules_path
        self.pm = pluggy.PluginManager("webos")
        self.pm.add_hookspecs(WebOSHookSpec)
        self.loaded_modules = []

    def discover_and_load(self):
        """
        Scan the modules directory and load all packages.
        """
        logger.info(f"Discovering modules in {self.modules_path}")
        
        # Get the physical path
        try:
            package = importlib.import_module(self.modules_path)
            package_path = Path(package.__file__).parent
        except Exception as e:
            logger.error(f"Could not find modules path {self.modules_path}: {e}")
            return

        for _, name, is_pkg in pkgutil.iter_modules([str(package_path)]):
            if is_pkg:
                module_name = f"{self.modules_path}.{name}"
                self._load_module(module_name)

    def _load_module(self, module_name: str):
        """
        Load a single module and register its hooks.
        """
        try:
            logger.debug(f"Loading module: {module_name}")
            module = importlib.import_module(module_name)
            
            # Register explicit hooks if they exist in hooks.py within the module
            try:
                hooks_module = importlib.import_module(f"{module_name}.hooks")
                self.pm.register(hooks_module)
                logger.debug(f"Registered hooks for {module_name}")
            except ImportError:
                # No explicit hooks, that's fine
                pass

            # Convention over Configuration: Auto-discover models and routers
            self.pm.register(AutoDiscoveryHooks(module_name))
            
            self.loaded_modules.append(module_name)
            logger.info(f"Module {module_name} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load module {module_name}: {e}")

    def get_all_models(self) -> List[Type[Document]]:
        """
        Collect all models from all modules via hooks.
        """
        all_models = []
        results = self.pm.hook.register_models()
        for models in results:
            if models:
                all_models.extend(models)
        return all_models

    def register_routes(self, app: FastAPI):
        """
        Trigger route registration hooks for all modules.
        """
        self.pm.hook.register_routes(app=app)

    def trigger_startup(self):
        """
        Trigger startup hooks.
        """
        self.pm.hook.on_startup()

    def trigger_shutdown(self):
        """
        Trigger shutdown hooks.
        """
        self.pm.hook.on_shutdown()

# Singleton instance for easy access
loader = ModuleLoader()
