import asyncio
import sys
from src.core.module_loader import loader

with open('debug_ui.log', 'w') as f:
    sys.stdout = f
    
    loader.discover_and_load()
    plugins = loader.pm.get_plugins()

    for p in plugins:
        has_ui = hasattr(p, 'register_ui')
        print(f"PLUGIN: {p} (has_register_ui={has_ui})")
        if hasattr(p, '__class__') and p.__class__.__name__ == 'DAMHooks':
            print('FOUND DAMHOOKS:', getattr(p, 'register_ui', None))
            p.register_ui()
            print('Called register_ui on DAMHooks successfully')
