import pluggy
from typing import Any

hookspec = pluggy.HookspecMarker("webos")
hookimpl = pluggy.HookimplMarker("webos")

class CoreHookSpecs:
    @hookspec
    async def post_setup(self) -> None:
        """Called after the kernel has been initialized and all modules discovered."""
        pass

    @hookspec
    async def on_module_load(self, module: Any) -> None:
        """Called when a new module is successfully loaded into the engine."""
        pass

    @hookspec
    def mount_ui(self) -> None:
        """Called to allow modules to register their UI components and routes."""
        pass

def get_plugin_manager() -> pluggy.PluginManager:
    pm = pluggy.PluginManager("webos")
    pm.add_hookspecs(CoreHookSpecs)
    return pm
