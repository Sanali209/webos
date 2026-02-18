import asyncio
import pytest
from datetime import datetime
from src.core.models import AuditMixin, CoreDocument
from pydantic import BaseModel

class SampleModel(AuditMixin):
    name: str

def test_audit_mixin_timestamps():
    # Test that default timestamps are created
    model = SampleModel(name="test")
    assert isinstance(model.created_at, datetime)
    assert isinstance(model.updated_at, datetime)
    assert (datetime.utcnow() - model.created_at).total_seconds() < 1

@pytest.mark.asyncio
async def test_core_document_settings():
    # Check the Settings class directly to avoid requiring Beanie initialization
    assert CoreDocument.Settings.use_revision is True
