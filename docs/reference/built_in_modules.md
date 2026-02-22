# Built-in Modules Reference

WebOS includes several heavily-featured plugin modules out of the box. These modules provide standard functionalities that most business applications require. They act as both core features and reference implementations for building your own applications.

## 1. Digital Asset Management (DAM)
**Location:** `src/modules/dam`

The DAM module is the most complex built-in application. It serves as an intelligent file repository with automatic tagging, thumbnail generation, and AI-driven metadata extraction.

### Key Models (`src.modules.dam.models`)

*   **`Asset`**: The primary entity representing a file. Inherits from `OwnedDocument` (ensuring user privacy isolation).
    *   *Features*: Tracks metadata, standardizes mime types, manages vectors, and stores detected AI objects.
*   **`Album`**: Virtual collections pointing to multiple assets.
*   **`Link`**: Represents directed edges establishing relationships between assets in a knowledge graph.

### Capabilities
- **Background Processing**: Enqueues workers via TaskIQ to run FFprobe, generating thumbnails and AI captions asynchronously when assets are uploaded.
- **Unified UI**: Custom grid layouts using AG Grid and Masonry for rendering thousands of images smoothly via NiceGUI.

---

## 2. Admin Settings & Registry
**Location:** `src/modules/admin`

The Admin module provides the central dashboard to manage the WebOS instance.

### Capabilities
- **Module Manager (`modules.py`)**: Uses the `ModuleLoader` to inspect which plugins are currently active on the framework.
- **Settings Editor (`settings.py`)**: Reads the `WebOSHookSpec.register_settings()` values from all modules and generates a dynamic UI to edit global configs persisted in `ModuleSettingsDoc`.
- **User Manager (`users.py`)**: An interface wrapped around FastAPI Users to promote/manage accounts.

---

## 3. Storage
**Location:** `src/modules/storage`

While the core defines the Abstract File System (AFS), the Storage module implements the concrete data source drivers.

### Capabilities
- **Local Disk Source**: Implements the `DataSource` interface to read/write files directly to the server's disk using `aiofiles`.
- **S3 Source** (Planned): Extendable architecture designed to add MinIO / Amazon S3 drivers.

---

## 4. File Commander
**Location:** `src/modules/file_commander`

A purely UI-driven module providing a dual-pane file manager interface.

### Capabilities
- **UI (`ui.py`)**: Uses the NiceGUI layout system to create an interactive, desktop-like file browser. It interacts directly with the Core `afs` (Abstract File System) to manipulate files.

---

## 5. Secure Vault
**Location:** `src/modules/vault`

A lightweight secrets manager demonstrating basic CRUD operations with encryption concepts.

### Key Models (`src.modules.vault.models`)

*   **`Secret`**: Stores a label, username, password, and notes. Inherits from `OwnedDocument` and `AuditMixin` (tracking created/updated timestamps automatically).
*   **`VaultSettings`**: A Pydantic model configuring auto-lock timeouts and encryption strategies.

```python
# Example of interacting with Vault Settings:
from src.modules.vault.models import VaultSettings

def get_default_vault_config():
    config = VaultSettings(auto_lock_timeout=300, enable_cloud_sync=False)
    return config
```

---

## 6. Authentication UI (`auth_ui`)
**Location:** `src/modules/auth_ui`

Provides the visual login, registration, and password recovery pages wrapping the backend FastAPI Users router. Registers itself to intercept unauthorized access.

---

## 7. Blogger
**Location:** `src/modules/blogger`

A complete blogging engine to publish, draft, and view markdown articles.
- **Model:** `BlogPost` Tracks title, slug, content (markdown), summary, and `status` ("draft" vs "published").

---

## 8. Cache
**Location:** `src/modules/cache`

Provides centralized, fast caching mechanisms to speed up the system across modules, preventing redundant recalculations or database hits.

---

## 9. Demo Modules
**Location:** `src/modules/demo_*`

A collection of non-production modules meant specifically to demonstrate the capabilities of the SDK.
- **`demo_hello_world`**: The absolute minimal viable web module, consisting of one basic string output route. Note: The tutorials base their examples on this.
- **`demo_dashboard`**: Shows how to construct a complex visual dashboard using standard NiceGUI widgets (charts, cards, stats).
- **`demo_data_explorer`**: Demonstrates the sheer power of the `DataExplorer` Auto-GUI SDK, mapping a complex model into an editable AG Grid.
- **`demo_report`**: Demonstrates generating HTML/PDF reports asynchronously via TaskIQ background jobs.

