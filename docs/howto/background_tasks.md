# How-To: Create Background Tasks

WebOS uses **TaskIQ** to offload long-running or resource-intensive operations (like report generation, data processing, or external API syncing) to background workers.

## 1. Defining a Task

To create a background task, use the `@task` decorator. We recommend putting your tasks in a `tasks.py` file within your module.

### Example
In `src/modules/your_module/tasks.py`:

```python
from src.core.tasks import broker

@broker.task
async def generate_complicated_report(data_id: str):
    # Simulate long work
    import asyncio
    await asyncio.sleep(10)
    
    return f"Report for {data_id} is complete!"
```

## 2. Triggering a Task

To trigger a task from your UI or API, call `.kiq()` on the task function.

### Example: From a UI Button
```python
from .tasks import generate_complicated_report

async def on_button_click():
    # This returns a TaskIQ handle, not the result!
    handle = await generate_complicated_report.kiq(data_id="123")
    ui.notify(f"Task started: {handle.task_id}")
```

## 3. Context Propagation

One of the key features of WebOS is that **User Context** and **Trace IDs** are automatically passed to the worker. 

Inside your task, you can access the `current_user`:

```python
from src.core.auth import current_user_id

@broker.task
async def my_task():
    uid = current_user_id.get()
    print(f"Executing task on behalf of user: {uid}")
```

## 4. Monitoring Progress (UI)

WebOS provides a `TaskProgressWidget` that you can add to your pages to show real-time feedback.

### Example
```python
from src.ui.components.task_progress import TaskProgressWidget

@ui.page("/my-report")
def report_page():
    with MainLayout():
        ui.label("Generate System Audit")
        
        # This widget polls the result backend and shows a progress bar
        TaskProgressWidget(task_id="...")
```

---

## Next Steps
- Learn how to [Manage Files](./file_ops.md).
- Understand the [Module System](../concepts/module_system.md).
- Explore the [Core Concepts](../tutorials/core_concepts.md).
