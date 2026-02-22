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
            if hasattr(package, "__path__"):
                package_path = Path(list(package.__path__)[0])
            elif hasattr(package, "__file__"):
                package_path = Path(package.__file__).parent
            else:
                logger.error(f"Module {self.modules_path} has no __path__ or __file__")
                return
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
                if hasattr(hooks_module, "hooks"):
                    self.pm.register(hooks_module.hooks)
                    logger.debug(f"Registered hooks instance for {module_name}")
                else:
                    self.pm.register(hooks_module)
                    logger.debug(f"Registered hooks module for {module_name}")
            except ModuleNotFoundError as e:
                # Only ignore if the hooks.py file itself is missing
                if e.name == f"{module_name}.hooks":
                    pass
                else:
                    logger.error(f"ModuleNotFoundError inside {module_name}.hooks: {e}")
            except Exception as e:
                logger.error(f"Error loading hooks for {module_name}: {e}")

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

    def get_all_asset_types(self) -> List[Any]:
        """
        Collect all asset types from all modules via hooks.
        """
        all_types = []
        results = self.pm.hook.register_asset_types()
        for types in results:
            if types:
                all_types.extend(types)
        return all_types

    def get_all_asset_drivers(self) -> List[Any]:
        """
        Collect all asset drivers from all modules via hooks.
        """
        all_drivers = []
        results = self.pm.hook.register_asset_drivers()
        for drivers in results:
            if drivers:
                all_drivers.extend(drivers)
        return all_drivers

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

    def register_module_services(self):
        """
        Trigger service registration hooks.
        """
        self.pm.hook.register_services()

    async def trigger_startup_async(self):
        """
        Trigger async startup hooks concurrently. Wait for all to finish.
        """
        import asyncio
        coros = self.pm.hook.on_startup_async()
        if coros:
            await asyncio.gather(*coros)

    def register_all_page_slots(self):
        """
        Trigger page slot registration hooks.
        """
        self.pm.hook.register_page_slots()

    def register_module_settings(self):
        """
        Collect settings schemas from all modules.
        """
        from src.core.services.settings_service import settings_service
        
        # We iterate through plugins to know which module is registering what
        for plugin in self.pm.get_plugins():
            if hasattr(plugin, "register_settings"):
                schema = plugin.register_settings()
                if schema:
                    # Determine module name
                    if hasattr(plugin, "module_name"):
                        module_name = plugin.module_name
                    else:
                        module_name = getattr(plugin, "__name__", "unknown")
                    
                    settings_service.register_schema(module_name, schema)

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
