# How-To: Protect a Route

This guide shows you how to restrict access to your module's API endpoints to authenticated users or administrators.

## 1. Basic Protection (Any Authenticated User)

To ensure a route can only be accessed by a logged-in user, use the `current_active_user` dependency from `src.core.auth`.

### Example
In `src/modules/your_module/router.py`:

```python
from fastapi import APIRouter, Depends
from src.core.auth import current_active_user, User

router = APIRouter()

@router.get("/my-profile")
async def get_my_data(user: User = Depends(current_active_user)):
    return {
        "email": user.email,
        "role": user.role,
        "message": "This is protected data!"
    }
```

## 2. Administrator Only Protection

To restrict a route to superusers only, use the `current_superuser` dependency.

### Example
```python
from src.core.auth import current_superuser

@router.delete("/system/reset")
async def reset_system(user: User = Depends(current_superuser)):
    # Dangerous logic here
    return {"status": "System reset by admin"}
```

## 3. User Data Isolation (Owned Records)

If you are working with database records belonging to a user, the best way to "protect" them is to inherit your model from `OwnedDocument`. The framework will then automatically filter all queries to show only the owner's records.

### Model Definition
In `src/modules/your_module/models.py`:
```python
from src.core.models import OwnedDocument

class Note(OwnedDocument):
    title: str
    content: str
```

### Route Usage
```python
@router.get("/notes")
async def list_notes(user: User = Depends(current_active_user)):
    # This automatically filters by user.id behind the scenes!
    notes = await Note.find_all().to_list()
    return notes
```

## 4. UI Protection (NiceGUI)

In your module's `ui.py`, you can check for the authenticated state via `app.storage.user`.

### Example
```python
from nicegui import app, ui

@ui.page("/my-secure-page")
def secure_page():
    if "user_id" not in app.storage.user:
        ui.notify("Please login first", type="negative")
        ui.navigate.to("/login")
        return
        
    ui.label("Welcome to your private dashboard!")
```

---

## Next Steps
- Learn how to [Add UI Elements](./add_ui_element.md).
- Understand the [Module System](../concepts/module_system.md).
