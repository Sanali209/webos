import asyncio
from src.core.kernel import Engine
from src.modules.task_manager.service import TaskService
from mongomock_motor import AsyncMongoMockClient

async def run_task_sample():
    engine = Engine()
    # Override the DB client for the sample to use mongomock
    engine.db.client = AsyncMongoMockClient()
    
    await engine.start()
    
    try:
        # Resolve the service from DI
        task_service = engine._di.resolve(TaskService)
        
        # 1. Create tasks
        await task_service.create_task("Finish Phase 2", "Implement the persistence layer and SDK.")
        await task_service.create_task("Review Architecture", "Ensure clean architecture boundaries.")
        
        # 2. List tasks
        tasks = await task_service.list_tasks()
        print(f"\n--- Current Tasks ({len(tasks)}) ---")
        for t in tasks:
            status = "[x]" if t.is_completed else "[ ]"
            print(f"{status} {t.title}: {t.description}")
        print("---------------------------\n")

    finally:
        await engine.stop()

if __name__ == "__main__":
    asyncio.run(run_task_sample())
