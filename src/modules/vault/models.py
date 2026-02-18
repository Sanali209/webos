from typing import Optional
from src.core.models import OwnedDocument, AuditMixin
from pydantic import Field

class Secret(OwnedDocument, AuditMixin):
    label: str
    username: str
    password: str
    website: Optional[str] = None
    notes: Optional[str] = None

    class Settings:
        name = "vault_secrets"
