from typing import Type
from pydantic import BaseModel
from src.core.hooks import hookimpl
from .models import VaultSettings

class VaultHooks:
    module_name = "vault"

    @hookimpl
    def register_settings(self) -> Type[BaseModel]:
        return VaultSettings

# Export the hooks object so pluggy can discover it
hooks = VaultHooks()
