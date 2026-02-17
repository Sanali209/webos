from typing import List, Optional
from src.core.service import BaseService
from src.core.infrastructure.persistence.beanie_adapter import BeanieRepository
from .domain import TaskItem
from .persistence import TaskDocument

class TaskRepository(BeanieRepository[TaskItem, TaskDocument]):
    def _to_entity(self, doc: TaskDocument) -> TaskItem:
        return TaskItem(
            id=str(doc.id),
            title=doc.title,
            description=doc.description,
            is_completed=doc.is_completed,
            due_date=doc.due_date
        )

    def _to_document(self, entity: TaskItem) -> TaskDocument:
        doc = TaskDocument(
            title=entity.title,
            description=entity.description,
            is_completed=entity.is_completed,
            due_date=entity.due_date
        )
        if entity.id:
            from bson import ObjectId
            doc.id = ObjectId(entity.id)
        return doc

class TaskService(BaseService[TaskItem]):
    def __init__(self, repository: TaskRepository):
        super().__init__()
        self.repo = repository

    async def create_task(self, title: str, description: str = None) -> TaskItem:
        return await self.execute_safely(
            "Create Task",
            self.repo.add,
            TaskItem(title=title, description=description)
        )

    async def list_tasks(self, include_completed: bool = True) -> List[TaskItem]:
        from src.core.filters import FilterCriteria, Operator
        criteria = FilterCriteria()
        if not include_completed:
            criteria.where("is_completed", Operator.EQ, False)
        
        return await self.execute_safely("List Tasks", self.repo.find, criteria)
