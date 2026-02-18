from pluggy import HookimplMarker
from .models import InventoryItem

hookimpl = HookimplMarker("webos")

class DemoDataExplorerHooks:
    module_name = "demo_data_explorer"

    @hookimpl
    def register_settings(self):
        # We skip settings registration for this demo module
        return None

    @hookimpl
    def register_ui(self):
        from . import ui

hooks = DemoDataExplorerHooks()
