# How-To: Manage Files (Unified Storage API)

WebOS uses an **Abstract File System (AFS)** that allows you to interact with local storage, S3, or other backends using a single, unified API and URN-based addressing.

## 1. Understanding URNs

Instead of using direct file paths, WebOS uses URNs in the format:
`fs://<source>/<path>`

- **Local Storage**: `fs://local/my_folder/file.txt` (Points to `./data/storage/` by default).
- **S3 Storage**: `fs://s3/backups/data.zip` (Points to the configured MinIO/S3 bucket).

## 2. Listing Directory Contents

To list files and folders, use `storage_manager.list_dir`.

### Example
```python
from src.core.storage import storage_manager

async def show_files():
    # Returns a list of FileMetadata objects
    items = await storage_manager.list_dir("fs://local/uploads")
    
    for item in items:
        status = "Folder" if item.is_dir else f"File ({item.size} bytes)"
        print(f"{item.name} - {status}")
```

## 3. Saving a File

To save data (bytes), use `storage_manager.save_file`.

### Example
```python
async def save_config(content: str):
    data_bytes = content.encode("utf-8")
    await storage_manager.save_file("fs://local/config/settings.json", data_bytes)
    print("Configuration saved successfully.")
```

## 4. Opening and Reading a File

To read a file, use `storage_manager.open_file`. Note that this returns an async binary stream.

### Example
```python
async def read_logs():
    async with await storage_manager.open_file("fs://local/logs/app.log") as f:
        content = await f.read()
        return content.decode("utf-8")
```

## 5. Why Use AFS?

Using the `storage_manager` ensures that your module remains **backend-agnostic**. You can develop locally using `fs://local` and deploy to production where the same URN points to an S3 bucket, without changing a single line of your module's logic.

---

## Next Steps
- Learn how to [Create Background Tasks](./background_tasks.md).
- Understand the [Module System](../concepts/module_system.md).
- Explore the [Core Concepts](../tutorials/core_concepts.md).
