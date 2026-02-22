from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any
from loguru import logger

@dataclass
class PageSlot:
    """Definition of an injectable UI area within a page."""
    path: str
    slot_name: str
    description: str = ""

class PageSlotRegistry:
    """
    Registry for cross-module UI injection.
    Allows modules to declare slots on their pages, and other modules to inject builders.
    """
    def __init__(self):
        # Maps (path, slot_name) -> PageSlot definition
        self._declarations: Dict[tuple[str, str], PageSlot] = {}
        # Maps (path, slot_name) -> list of builder functions
        self._injections: Dict[tuple[str, str], List[Callable]] = {}

    def declare(self, path: str, slot_name: str, description: str = ""):
        """Declare that a page has an injectable slot available."""
        key = (path, slot_name)
        if key not in self._declarations:
            self._declarations[key] = PageSlot(path, slot_name, description)
            self._injections[key] = []
            logger.debug(f"PageSlot declared: {path} -> {slot_name}")

    def inject(self, path: str, slot_name: str, builder: Callable):
        """Inject a component builder into a declared slot."""
        key = (path, slot_name)
        if key not in self._declarations:
            logger.warning(f"Attempted to inject into undeclared PageSlot: {path} -> {slot_name}")
            # We still allow injection even if undeclared to support load-order independence
            self._injections[key] = []
        
        self._injections[key].append(builder)
        logger.debug(f"Component injected into PageSlot: {path} -> {slot_name}")

    def render(self, path: str, slot_name: str, **kwargs):
        """Render all injected components for the slot."""
        key = (path, slot_name)
        builders = self._injections.get(key, [])
        for builder in builders:
            try:
                builder(**kwargs)
            except Exception as e:
                logger.error(f"Error rendering PageSlot {path}->{slot_name}: {e}")

# Singleton registry
page_slot_registry = PageSlotRegistry()
