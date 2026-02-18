from src.core.module_loader import loader
from src.ui.registry import ui_registry

def check_ui():
    print("\n" + "="*50)
    print("WebOS UI Registration Diagnostic")
    print("="*50)
    
    # 1. Load Modules
    loader.discover_and_load()
    
    # 2. Trigger UI Hooks
    loader.register_ui()
    
    print(f"\nTotal Apps Registered: {len(ui_registry.apps)}")
    for app in ui_registry.apps:
        print(f" - [{app.category}] {app.name} ({app.route}) icon: {app.icon}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    check_ui()
