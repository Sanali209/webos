import asyncio
from src.core.module_loader import loader
from src.ui.registry import ui_registry
from src.ui.admin_registry import admin_registry

async def debug_all():
    print("--- STARTING MODULE DISCOVERY ---")
    loader.discover_and_load()
    
    print("\n--- REGISTERING UI ---")
    try:
        loader.register_ui()
    except Exception as e:
        print('register_ui failed:', e)
        
    print("\n--- REGISTERING ADMIN WIDGETS ---")
    try:
        loader.register_admin_widgets()
    except Exception as e:
        print('register_admin_widgets failed:', e)
        
    print("\n================ FINAL REGISTRY STATE ================")
    print('UI Apps Loaded in Registry:')
    for a in ui_registry.apps:
        print(f" - {a.name} ({a.route})")
    
    print('\nAdmin Widgets Loaded in Registry:')
    for w in admin_registry.get_widgets():
        print(f" - {w.__class__.__name__} (from {w.name})")

if __name__ == "__main__":
    asyncio.run(debug_all())
