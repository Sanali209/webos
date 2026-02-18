import pluggy
from fastapi import FastAPI
from beanie import Document
from typing import List, Type

hookspec = pluggy.HookspecMarker("webos")
hookimpl = pluggy.HookimplMarker("webos")

class WebOSHookSpec:
    """
    Hook specifications for WebOS modules.
    Modules can implement these hooks to extend system behavior.
    """

    @hookspec
    def register_models() -> List[Type[Document]]:
        """
        Register Beanie models for this module.
        Should return a list of Document classes.
        """

    @hookspec
    def register_routes(app: FastAPI):
        """
        Hook to register FastAPI routes (via router.py).
        """

    @hookspec
    def register_ui():
        """
        Hook to register NiceGUI pages and components.
        """

    @hookspec
    def register_data_sources(afs):
        """
        Hook to register storage backends with the AFS.
        """

    @hookspec
    def register_tasks(broker):
        """
        Hook to register background tasks with TaskIQ broker.
        """

    @hookspec
    def register_admin_widgets():
        """
        Hook to register cards/widgets for the Admin Dashboard.
        Modules should return a list of widgets or register them via a registry.
        """

    @hookspec
    def on_startup():
        """
        Logic to run during application startup.
        """

    @hookspec
    def on_shutdown():
        """
        Logic to run during application shutdown.
        """
