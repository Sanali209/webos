# Tutorial: Create Your First Module

In this tutorial, we will build a minimal plugin module. WebOS uses convention-over-configuration, so simply creating files in the right place allows the `ModuleLoader` to discover them.

## 1. Create the Module Folder

Create a new directory in `src/modules/` called `hello_world`.

## 2. Create the API Router

If a module contains a `router.py`, the system will automatically mount it to the REST API prefix `/api/hello_world`.

Create `src/modules/hello_world/router.py`:

```python
# Example: Creating an auto-discovered API route
from fastapi import APIRouter

router = APIRouter()

@router.get("/ping")
async def ping():
    return {"message": "pong"}
```

*Test it:* Start the server (`python run.py`) and visit `http://localhost:8000/docs`. You will see `/api/hello_world/ping` automatically documented.

## 3. Create a Database Model

If a module contains a `models.py` with classes inheriting from `Document` or `CoreDocument`, they are automatically registered with Beanie on startup.

Create `src/modules/hello_world/models.py`:

```python
# Example: Creating an auto-discovered Beanie Document
from beanie import Document
from pydantic import Field

class GreetingRecord(Document):
    message: str = Field(..., description="The greeting text")
    count: int = 0
```

## 4. Register a UI Component

To show up in the NiceGUI frontend, we use Pluggys `WebOSHookSpec`.

Create `src/modules/hello_world/__init__.py`:

```python
# Example: Using hooks to register UI navigation
from nicegui import ui
from src.core.hooks import hookimpl
from src.ui.registry import ui_registry

@hookimpl
def register_ui():
    @ui.page('/hello')
    def hello_page():
        ui.label('Hello World Module!').classes('text-2xl font-bold')

    # Add a link to the main app launcher
    ui_registry.register_app(
        name="Hello World",
        icon="waving_hand",
        route="/hello"
    )
```

## Conclusion

Restart the server. You should now see a "Hello World" icon in the UI launcher and the `/api/hello_world/` routes in the Swagger docs.
