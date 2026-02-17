import pytest
import asyncio
from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from mongomock_motor import AsyncMongoMockClient as MockClient
from pydantic import BaseModel
from typing import Optional

from src.core.infrastructure.persistence.beanie_adapter import BeanieRepository
from src.core.infrastructure.persistence.models import CoreDocument
from src.core.filters import FilterCriteria, Operator

# Domain Entity
class TaskEntity(BaseModel):
    id: Optional[str] = None
    title: str
    completed: bool = False

# Beanie Document
class TaskDocument(CoreDocument):
    title: str
    completed: bool = False
    
    class Settings:
        name = "tasks_test"

# Repository Implementation
class TaskRepository(BeanieRepository[TaskEntity, TaskDocument]):
    def _to_entity(self, doc: TaskDocument) -> TaskEntity:
        return TaskEntity(id=str(doc.id), title=doc.title, completed=doc.completed)

    def _to_document(self, entity: TaskEntity) -> TaskDocument:
        # Use existing id if present during update
        doc = TaskDocument(title=entity.title, completed=entity.completed)
        if entity.id:
            from bson import ObjectId
            doc.id = ObjectId(entity.id)
        return doc

@pytest.fixture(autouse=True, scope="function")
async def init_mock_db():
    client = MockClient()
    await init_beanie(database=client.get_database("test_db"), document_models=[TaskDocument])
    yield
    # Cleanup if needed

@pytest.mark.asyncio
async def test_beanie_repo_lifecycle():
    repo = TaskRepository(TaskDocument)
    
    # 1. Create
    task = TaskEntity(title="Learn Clean Architecture")
    created = await repo.add(task)
    assert created.id is not None
    assert created.title == "Learn Clean Architecture"
    
    # 2. Get
    fetched = await repo.get(created.id)
    assert fetched.title == created.title
    
    # 3. Find with criteria
    criteria = FilterCriteria.eq("title", "Learn Clean Architecture")
    results = await repo.find(criteria)
    assert len(results) == 1
    assert results[0].id == created.id
    
    # 4. Count
    count = await repo.count(criteria)
    assert count == 1
    
    # 5. Delete
    deleted = await repo.delete(created.id)
    assert deleted is True
    
    # 6. Verify deletion
    none_found = await repo.get(created.id)
    assert none_found is None
