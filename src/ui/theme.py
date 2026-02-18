from nicegui import ui

class Theme:
    """
    Central design system for WebOS.
    Uses Tailwind classes to define a premium, modern look.
    """
    
    # Color Palette (Tailwind-based)
    PRIMARY = "primary" # NiceGUI default or mapped to 'blue-600'
    SECONDARY = "bg-slate-100"
    DARK_BG = "bg-slate-900"
    DARK_TEXT = "text-slate-100"
    
    # Layout Constants
    SIDEBAR_WIDTH = "w-64"
    HEADER_HEIGHT = "h-16"

    @staticmethod
    def apply_standard_card(element):
        """Applies a premium glassmorphic/modern card style."""
        element.classes("bg-white border border-slate-200 rounded-xl shadow-sm p-4 hover:shadow-md transition-all")

    @staticmethod
    def toggle_dark_mode():
        """Toggles the global dark mode via NiceGUI."""
        dark = ui.dark_mode()
        dark.toggle()
        ui.notify(f"Theme switched to {'Dark' if dark.value else 'Light'}")

# Global instance
theme = Theme()
