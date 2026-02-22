from src.core.module_loader import loader
from src.ui.registry import ui_registry

print("DISCOVERING")
loader.discover_and_load()
print("REGISTERING UI")
loader.register_ui()
print('APPS:', [a.route for a in ui_registry.apps])
