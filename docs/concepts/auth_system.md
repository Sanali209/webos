# Authentication & Security

WebOS provides a multi-layered security model that combines standard FastAPI Users authentication with custom row-level isolation and role-based access control (RBAC).

## 1. Authentication Flow

WebOS uses **JWT (JSON Web Tokens)** for authentication.
- **Login**: `POST /api/auth/jwt/login` returns an `access_token`.
- **Authorization**: The token is sent in the `Authorization: Bearer <token>` header for subsequent requests.
- **Persistence**: For the NiceGUI shell, the `user_id` is persisted in `app.storage.user` (session cookie protected by `SECRET_KEY`).

## 2. Context Propagation

To ensure that the "current user" is available throughout the entire application lifecycle (including background tasks), WebOS uses `contextvars`.

- **Middleware**: The `set_task_context` dependency in `main.py` captures the authenticated user from the request.
- **Context Variable**: The `user_id_context` (in `src.core.middleware`) is set for every request.
- **Task Propagation**: The `ContextPropagationMiddleware` (TaskIQ) automatically injects the `user_id` into task headers so workers know who triggered the task.

## 3. Data Isolation: `OwnedDocument`

The most powerful security feature in WebOS is the `OwnedDocument` mixin. It provides **automatic row-level security**.

If your model inherits from `OwnedDocument`:
1. It adds an `owner_id` field.
2. The framework (via Beanie) enforces that users can only `find` or `update` documents where `owner_id == current_user_id`.

```python
from src.core.models import OwnedDocument

# This secret will ONLY be visible to the user who created it
class Secret(OwnedDocument):
    label: str
    password: str
```

## 4. Role-Based Access Control (RBAC)

WebOS support fine-grained permissions via the `role` field on the `User` model.

### Route Protection
You can protect routes using the `current_active_user` or `current_superuser` dependencies:

```python
from src.core.auth import current_superuser

@router.get("/admin-only")
async def sensitive_data(user: User = Depends(current_superuser)):
    return {"data": "confidential"}
```

---

## Next Steps
- Follow the [How-To: Protect a Route](../howto/protect_route.md).
- Learn about [Module Auto-Discovery](./module_system.md).
