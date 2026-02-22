# Data Management

This document explains how WebOS models, persists, and accesses data across its modular architecture, utilizing **MongoDB**, the **Beanie ODM**, and the **Abstract File System (AFS)**.

## MongoDB and Beanie ODM

WebOS heavily relies on MongoDB for flexible, schema-less document storage. We use **Beanie**, an asynchronous ODM (Object Document Mapper), to interface with MongoDB. Beanie models are defined using standard Python type hints via Pydantic.

### Module Data Isolation and Discovery

In a modular system, the Core does not know about the business models (e.g. `Invoice`, `UserAsset`, `BlogPost`) in advance. The `ModuleLoader` discovers models dynamically.

There are two ways models are registered:
1. **Auto-Discovery**: Any Pydantic/Beanie document defined in a module's `models.py` is automatically registered with the database upon startup.
2. **Explicit Hooks**: Modules can implement the `register_models()` hook to return a list of Beanie documents if they are stored outside of the standard `models.py`.

During application startup (`lifespan` in `main.py`), the Core gathers all models and runs `init_db(all_models)` at once.

### Cross-Module Data Access

One of the strict constraints of the Modular Monolith is that Module A should not directly query Module B's database collections, nor should it establish hard compilation dependencies.

To establish relationships safely, use Beanie's `Link` feature with string-based resolution, relying on the central document registry rather than direct imports.

```python
# Assuming this is in the Billing module, referencing the Core User model:
from beanie import Document, Link

class Invoice(Document):
    amount: float
    # Safely linking to a model in a different module without importing it
    user: Link["User"]
```

## The Abstract File System (AFS)

For binary data and persistent file storage, WebOS uses an Abstract File System (`src.core.storage`). This allows the application to remain agnostic about whether files are stored locally on disk, in Amazon S3, or via another provider.

*   **URN-based Addressing**: Files are universally referenceable via URNs, e.g., `fs://local/uploads/resume.pdf` or `fs://s3/assets/video.mp4`.
*   **Data Sources**: Modules can register their own custom `DataSource` providers by hooking into `register_data_sources(afs)`.

---

**Full reference**: See [Core API Reference](../reference/core_api.md) for how to use the AFS and Storage APIs.
