# Tutorial: Create Your First Module

This step-by-step guide will teach you how to build a simple "Hello World" module that includes a database model, an API endpoint, and a UI page integrated into the WebOS Launchpad.

## 1. Create the Module Folder

Create a new directory in `src/modules/` and add an empty `__init__.py` file to make it discoverable.

```bash
mkdir src/modules/hello_world
touch src/modules/hello_world/__init__.py
```

## 2. Define a Data Model

Create `src/modules/hello_world/models.py`. We'll create a simple model to store greetings.

```python
from src.core.models import CoreDocument
from beanie import Document

class Greeting(CoreDocument):
    message: str
    recipient: str

    class Settings:
        name = "greetings"
```

## 3. Create an API Endpoint

Create `src/modules/hello_world/router.py`. This will allow us to create greetings via HTTP.

```python
from fastapi import APIRouter
from .models import Greeting

router = APIRouter()

@router.post("/greetings")
async def create_greeting(message: str, recipient: str):
    greeting = Greeting(message=message, recipient=recipient)
    await greeting.save()
    return greeting
```

## 4. Build the UI Page

Create `src/modules/hello_world/ui.py`. This uses NiceGUI to create a visual interface and registers the app with the WebOS Launchpad.

```python
from nicegui import ui
from src.ui.layout import MainLayout
from src.ui.registry import ui_registry, AppMetadata
from src.core.hooks import hookimpl
from .models import Greeting

@ui.page("/hello")
async def hello_page():
    with MainLayout():
        ui.label("Hello World Module").classes("text-3xl font-black")
        
        # Display existing greetings
        greetings = await Greeting.find_all().to_list()
        for g in greetings:
            ui.label(f"{g.message}, {g.recipient}!")

@hookimpl
def register_ui():
    """Register the Hello World App on the Launchpad."""
    ui_registry.register_app(AppMetadata(
        name="Hello World",
        icon="waving_hand",
        route="/hello",
        description="My very first WebOS module."
    ))
```

## 5. Verify Your Module

1. **Restart the Server**: WebOS will auto-discover your new files.
2. **Check the Launchpad**: You should see a new "Hello World" icon.
3. **Visit the Page**: Click the icon or go to [http://localhost:8000/hello](http://localhost:8000/hello).
4. **Test the API**: Open Swagger UI at [http://localhost:8000/api/docs](http://localhost:8000/api/docs) and try the `POST /api/greetings` endpoint.

---

## Next Steps
- Learn how to [Protect a Route](../howto/protect_route.md).
- Understand the [UI & Layout System](../concepts/layout_system.md).
- Explore the [Event Bus](../tutorials/core_concepts.md).
