from typing import Any, Coroutine, List, Protocol, Type, Union
from fastapi import APIRouter, FastAPI
from beanie import Document
from pluggy import HookimplMarker, HookspecMarker
from pydantic import BaseModel

hookspec = HookspecMarker("webos")
hookimpl = HookimplMarker("webos")

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
    def register_settings() -> Type[BaseModel]:
        """
        Register a Pydantic model class representing the module's settings.
        Settings will be persisted in the system_settings collection.
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
