from typing import Optional
from pydantic import BaseModel, Field
from src.core.models import OwnedDocument, AuditMixin

class VaultSettings(BaseModel):
    """Configuration for the Secure Vault module."""
    auto_lock_timeout: int = Field(600, description="Auto-lock timeout in seconds")
    enable_cloud_sync: bool = Field(False, description="Enable synchronization with cloud storage")
    encryption_algorithm: str = Field("AES-256", description="Encryption algorithm to use")

class Secret(OwnedDocument, AuditMixin):
    label: str
    username: str
    password: str
    website: Optional[str] = None
    notes: Optional[str] = None

    class Settings:
        name = "vault_secrets"
