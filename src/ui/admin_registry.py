from typing import List, Callable, Dict
from dataclasses import dataclass

@dataclass
class AdminWidget:
    name: str
    component: Callable
    icon: str = "widgets"
    description: str = ""
    column_span: int = 1

class AdminRegistry:
    """Registry for Admin Dashboard widgets."""
    def __init__(self):
        self._widgets: List[AdminWidget] = []

    def register_widget(self, widget: AdminWidget):
        self._widgets.append(widget)

    def get_widgets(self) -> List[AdminWidget]:
        return self._widgets

admin_registry = AdminRegistry()
