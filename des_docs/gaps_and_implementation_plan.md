# Gap Analysis and Implementation Plan

## Executive Summary
This document outlines the identified gaps, placeholders, and demo implementations within the WebOS Framework. It provides a strategic plan to replace these with production-ready code, focusing on robust authentication, a fully functional dashboard system, and the removal of tutorial artifacts.

## 1. Identified Gaps & Placeholders

The following areas require immediate attention to transition the framework from a demonstration state to a production-ready system:

### 1.1 Authentication & Authorization
*   **Blogger Module (`src/modules/blogger/ui.py:51`):** Contains a placeholder comment `# In a real app, check auth here. For demo, we just show it.`
*   **DAM Module (`src/modules/dam/ui/upload_dialog.py:21`):** Uses a hardcoded `TODO_AUTH_TOKEN` string instead of a real session token.
*   **Vault Module (`src/modules/vault/ui.py`):** Relies on manual checks of `user_id_context` within the UI logic rather than a centralized route guard.

### 1.2 File Management & Drivers
*   **FilePicker Component (`src/ui/components/file_picker.py:40`):** Directory navigation is explicitly disabled with a `ui.notify` message: `"Navigation not implemented in demo file picker"`.
*   **Video Driver (`src/modules/dam/drivers/video_driver.py`):** Relies on `ffprobe` being in the system PATH. If missing, metadata extraction is disabled. This needs better error handling or a bundled dependency strategy.

### 1.3 Demo Modules
Several modules exist purely for tutorial purposes and need to be removed or replaced:
*   `src/modules/demo_dashboard`: A hardcoded dashboard with fake data.
*   `src/modules/demo_hello_world`: Basic "Hello World" example.
*   `src/modules/demo_report`: Demonstrates background tasks.
*   `src/modules/demo_data_explorer`: Sample data for the Data Explorer SDK.

### 1.4 Admin & Settings
*   **Settings Page (`src/modules/admin/settings.py:37`):** The "Save Changes" button is disabled with the label `"Read-only in demonstration mode."`

---

## 2. Authentication Strategy Implementation

The framework currently uses `FastAPI Users` with JWT strategy (`src/core/auth.py`), but it is not consistently applied across all UI modules.

### 2.1 Centralized Auth Guard
Instead of manual checks in every page function, we will implement a Python decorator `@login_required` or a middleware hook for NiceGUI pages.

**Proposed Implementation Pattern:**
```python
from functools import wraps
from nicegui import ui
from src.core.auth import current_active_user

def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check current session or JWT token
        if not app.storage.user.get("user_id"):
             ui.navigate.to("/login")
             return
        return await func(*args, **kwargs)
    return wrapper

@ui.page("/dashboard")
@login_required
async def dashboard_page():
    ...
```

### 2.2 Extending Vault Authentication
The `Vault` module's ownership model (`owner_id`) is sound but needs to be standardized. We will:
1.  **Enforce Ownership at the Service Layer:** Ensure `BaseDocument` queries always filter by `owner_id` unless the user is a superuser.
2.  **Session Management:** Ensure the `user_id` from the JWT token is automatically propagated to `user_id_context` for every request, including WebSocket connections used by NiceGUI.

---

## 3. Fully Functional Dashboard Architecture

We will replace the static `demo_dashboard` with a dynamic, widget-based system.

### 3.1 Architecture
*   **Dashboard Module:** A new core module `src/modules/dashboard` that acts as a container.
*   **Widget Registry:** A mechanism for other modules (Blogger, DAM, Vault) to register "widgets" (small UI components) that the Dashboard can render.

### 3.2 Widget Interface
Modules will register widgets via a hook, providing metadata and a render function.

```python
# In src/core/hooks.py or similar
class DashboardWidget:
    name: str
    size: str  # e.g., "1x1", "2x1"
    render: Callable  # Function to draw the NiceGUI component

# Example: Vault registering a widget
@hookimpl
def register_dashboard_widgets():
    return [
        DashboardWidget(
            name="Recent Secrets",
            size="1x1",
            render=lambda: ui.label(f"{len(secrets)} secrets stored")
        )
    ]
```

### 3.3 User Customization
*   Store user preferences (widget layout, visibility) in a `UserDashboardSettings` model in MongoDB.
*   Allow users to drag-and-drop or toggle widgets on their dashboard.

---

## 4. Module Cleanup & Enhancements

### 4.1 Remove Demo Modules
The following directories will be deleted:
*   `src/modules/demo_dashboard/`
*   `src/modules/demo_hello_world/`
*   `src/modules/demo_report/`
*   `src/modules/demo_data_explorer/`

### 4.2 Fix FilePicker
We will implement the navigation logic in `src/ui/components/file_picker.py`:
*   Update `handle_select` to update `self.current_path` when a directory is clicked.
*   Add a "Go Up" (`..`) button to navigate to the parent directory.
*   Implement breadcrumbs for better UX.

### 4.3 Robust Video Processing
*   **Dependency Check:** Add a startup check in `src/core/startup.py` that warns explicitly if `ffprobe` or `ffmpeg` is missing.
*   **Docker Integration:** Ensure the Dockerfile includes `ffmpeg` installation so it works out-of-the-box in containerized environments.

### 4.4 Enable Admin Settings
*   Remove the `disabled` prop from the "Save Changes" button in `src/modules/admin/settings.py`.
*   Connect the button to the `settings_service.update()` method.

---

## 5. Implementation Roadmap

1.  **Phase 1: Foundation & Cleanup**
    *   Delete demo modules.
    *   Implement `AuthGuard` decorator.
    *   Enable Admin Settings saving.

2.  **Phase 2: Core Components**
    *   Complete `FilePicker` navigation.
    *   Harden `VideoDriver` and Docker environment.

3.  **Phase 3: Dashboard System**
    *   Create `src/modules/dashboard`.
    *   Define `DashboardWidget` protocol.
    *   Update `Vault`, `Blogger`, and `DAM` to register widgets.

4.  **Phase 4: Security Audit**
    *   Apply `AuthGuard` to all sensitive routes.
    *   Verify `owner_id` isolation across all data models.
