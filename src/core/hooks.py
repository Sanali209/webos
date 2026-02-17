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
    def register_models(self) -> List[Type[Document]]:
        """
        Register Beanie models for this module.
        Should return a list of Document classes.
        """

    @hookspec
    def register_routes(self, app: FastAPI):
        """
        Register FastAPI routes for this module.
        """

    @hookspec
    def on_startup(self):
        """
        Logic to run during application startup.
        """

    @hookspec
    def on_shutdown(self):
        """
        Logic to run during application shutdown.
        """
