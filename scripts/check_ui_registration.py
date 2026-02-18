import sys
import os
from loguru import logger

# Add project root to PYTHONPATH
sys.path.append(os.getcwd())

from src.core.module_loader import loader
from src.ui.registry import ui_registry

def check_apps():
    print("🔍 Discovering modules...")
    loader.discover_and_load()
    
    # We need to trigger the hooks to actually register the UI
    print("🎨 Registering UI components...")
    loader.register_ui()
    
    print(f"\n✅ Found {len(ui_registry.apps)} registered apps:")
    for i, app in enumerate(ui_registry.apps, 1):
        print(f"{i}. {app.name} (Route: {app.route}, Icon: {app.icon}, System: {app.is_system})")

if __name__ == "__main__":
    check_apps()
