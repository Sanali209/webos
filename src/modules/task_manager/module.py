from src.core.module import BaseModule
from src.core.infrastructure.persistence.beanie_adapter import DatabaseManager
from .service import TaskService, TaskRepository
from .persistence import TaskDocument

class TaskManagerModule(BaseModule):
    @property
    def name(self) -> str:
        return "task_manager"

    @property
    def version(self) -> str:
        return "0.1.0"

    async def initialize(self):
        # 1. Register Persistence Model
        db_manager = self._di.resolve(DatabaseManager)
        db_manager.register_model(TaskDocument)
        
        # 2. Register Services in DI
        # We manually register the repository and service for this module
        repo = TaskRepository(TaskDocument)
        service = TaskService(repo)
        
        self._di.register(TaskRepository, instance=repo)
        self._di.register(TaskService, instance=service)
        
        self.logger.info("Task Manager Module initialized and services registered.")
