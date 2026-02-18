from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class AppMetadata:
    """Metadata for a WebOS App/Module to be shown in the UI."""
    name: str
    icon: str
    route: str
    description: str = ""
    category: str = "Utilities"
    is_system: bool = False
    commands: List[str] = field(default_factory=list)

class UIRegistry:
    """
    Central registry for UI-related metadata.
    Used to build the Navigation Sidebar and the Launchpad (App Grid).
    """
    def __init__(self):
        self.apps: List[AppMetadata] = []

    def register_app(self, metadata: AppMetadata):
        """Register a new app/module for inclusion in Launchpad and Sidebar."""
        # Prevent duplicate registrations by route
        if any(app.route == metadata.route for app in self.apps):
            return
        self.apps.append(metadata)

# Global Registry Instance
ui_registry = UIRegistry()
