import importlib
import pkgutil
from pathlib import Path
from typing import List, Type, Dict, Any

import pluggy
from beanie import Document
from fastapi import FastAPI
from loguru import logger

from src.core.hooks import WebOSHookSpec, hookimpl

class AutoDiscoveryPlugin:
    def __init__(self, module_name: str):
        self.module_name = module_name

    @hookimpl
    def register_models(self) -> List[Type[Document]]:
        try:
            models_mod_name = f"{self.module_name}.models"
            logger.debug(f"Auto-discovering models in {models_mod_name}")
            models_mod = importlib.import_module(models_mod_name)
            models = []
            for attr_name in dir(models_mod):
                attr = getattr(models_mod, attr_name)
                if isinstance(attr, type) and issubclass(attr, Document) and attr is not Document:
                    models.append(attr)
            if models:
                logger.debug(f"Found models in {self.module_name}: {[m.__name__ for m in models]}")
            return models
        except ImportError:
            return []
        except Exception as e:
            logger.error(f"Error discovering models in {self.module_name}: {e}")
            return []

    @hookimpl
    def register_routes(self, app: FastAPI):
        try:
            router_mod_name = f"{self.module_name}.router"
            logger.debug(f"Auto-discovering routes in {router_mod_name}")
            router_mod = importlib.import_module(router_mod_name)
            if hasattr(router_mod, "router"):
                app.include_router(router_mod.router)
                logger.debug(f"Mounted router for {self.module_name}")
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Error discovering routes in {self.module_name}: {e}")

def create_autodiscovery_hooks(module_name: str):
    """Factory to create a plugin object for a specific module's auto-discovery."""
    return AutoDiscoveryPlugin(module_name)

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
            self.pm.register(create_autodiscovery_hooks(module_name))

            # Auto-discover ui.py if it exists
            ui_module_name = f"{module_name}.ui"
            try:
                # We want to know if the file exists but fails to import due to other errors
                # pkgutil.get_loader can check if the module exists without importing it fully
                ui_loader = pkgutil.get_loader(ui_module_name)
                if ui_loader:
                    ui_module = importlib.import_module(ui_module_name)
                    self.pm.register(ui_module)
                    logger.debug(f"Auto-registered UI hooks for {module_name}")
            except Exception as e:
                logger.error(f"Failed to auto-register UI logic for {module_name}: {e}")
            
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

    def register_ui(self):
        """
        Trigger UI registration hooks for all modules.
        """
        self.pm.hook.register_ui()

    def register_data_sources(self, afs):
        """
        Trigger data source registration hooks for all modules.
        """
        self.pm.hook.register_data_sources(afs=afs)

    def register_tasks(self, broker):
        """
        Trigger task registration hooks for all modules.
        """
        self.pm.hook.register_tasks(broker=broker)

    def register_admin_widgets(self):
        """
        Trigger admin widget registration hooks.
        """
        self.pm.hook.register_admin_widgets()

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
