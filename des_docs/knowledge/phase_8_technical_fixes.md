# KI: Authentication and Persistence Patterns in WebOS (Phase 8 Fixes)

This Knowledge Item documents the technical solutions for authentication persistence, TaskIQ serialization, and UI rendering bugs encountered during the Phase 8 integration.

## 1. Authentication Persistence with NiceGUI

### Issue: `AttributeError: module 'nicegui.ui' has no attribute 'storage'`
In NiceGUI 2.0+, the persistent storage is accessed via `nicegui.app.storage` rather than `nicegui.ui.storage`. Using the wrong attribute causes 500 server errors.

### Best Practice
```python
from nicegui import app, ui

# Set storage
app.storage.user['user_id'] = '...'

# Read storage
uid = app.storage.user.get('user_id')
```
**Requirement**: You MUST set `storage_secret` in `ui.run_with(..., storage_secret=settings.SECRET_KEY)`.

---

## 2. TaskIQ Context Propagation

### Issue: `PydanticSerializationError`
TaskIQ middleware propagates headers using Pydantic. If a `ContextVar` has a default value that is a lambda or a non-serializable object (like `uuid.uuid4`), serializing the message will fail if that context is used.

### Solution
- Use `None` as the default for `ContextVar`.
- Handle initialization (e.g., generating a `trace_id`) inside the middleware's `pre_send` method.

```python
# GOOD
trace_id_context: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

# Inside middleware
trace_id = trace_id_context.get() or str(uuid.uuid4())
```

---

## 3. UI Closure Capture in Loops

### Issue: "Stuck" Navigation Routes
When creating multiple UI components in a loop (e.g., app cards in a grid) and assigning click handlers:
```python
for app in apps:
    ui.card().on('click', lambda: ui.navigate.to(app.route)) # WRONG: Always uses the last app
```
All cards will navigate to the *last* app's route because the lambda captures the variable `app` by reference.

### Fix
Use a default argument to capture the *current value* of the variable at definition time:
```python
for app in apps:
    ui.card().on('click', lambda a=app: ui.navigate.to(a.route)) # CORRECT
```

---

## 4. Fresh Startup Seeding

### Pattern: Conditional Seeding
To ensure an "out of the box" experience while preserving user data:
1. Check if the user table is empty: `await User.count() == 0`.
2. If empty, seed the default admin (`admin@webos.io` / `admin123`).
3. Call this check in the FastAPI `lifespan` handler *after* database initialization.
