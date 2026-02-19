
### 3.1. Performance Bottlenecks
- **Synchronous Hashing**: Calculating SHA-256 for large files (e.g., 4GB video) in the main thread (even if `async` def, CPU-bound work blocks) will freeze the application.
    - **Risk**: High.
    - **Mitigation**: Hashing must be done in chunks and ideally offloaded to a thread pool or calculated during the stream read without blocking the event loop.
- **Python-Magic Overhead**: Loading `libmagic` database for every file can be slow.
    - **Risk**: Low/Medium.
    - **Mitigation**: Ensure the `magic` instance is a singleton or reused.

### 3.2. Concurrency & Integrity
- **CAS Race Conditions**: The "Check-then-Act" logic in `AssetService` (Check Hash -> If Not Exists -> Write) is prone to race conditions if two users upload the same file simultaneously.
    - **Risk**: Medium.
    - **Mitigation**: Implement a distributed lock (e.g., Redis Lock via `TaskIQ` or `Redlock`) on the hash key during ingestion.
- **File System Atomicity**: Simply writing to `fs://storage/cas/...` might leave partial files if the process crashes.
    - **Risk**: Medium.
    - **Mitigation**: Write to a temporary location first, then atomically move/rename to the final CAS path.

### 3.3. Scalability
- **MongoDB Text Search**: While sufficient for <100k assets, MongoDB's text search lacks advanced features (fuzzy search, relevance tuning) compared to dedicated engines.
    - **Risk**: Low (for current scale).
    - **Mitigation**: Acceptable for MVP. Plan for an optional Elasticsearch/Meilisearch integration in Phase 3.
- **Watchdog Limitations**: `watchdog` relies on OS primitives (inotify/kqueue). Watching massive directory trees can hit system limits.
    - **Risk**: Medium.
    - **Mitigation**: distinct config for "Watch" vs "Scan Interval".

### 3.4. User Experience
- **Processing State**: The design mentions async processing, but the Data Model (`Asset`) lacks a clear "Status" field (e.g., `PENDING`, `PROCESSING`, `READY`, `FAILED`).
    - **Risk**: Medium.
    - **Mitigation**: Add `status` field to `Asset` so the UI can show a spinner/progress bar while thumbnails/metadata are generating.

## 4. Recommendations

1.  **Add `processing_status` to `Asset` model**:
    ```python
    class AssetStatus(str, Enum):
        UPLOADING = "uploading"
        PROCESSING = "processing"
        READY = "ready"
        ERROR = "error"
    ```
2.  **Implement Stream Hashing**: Calculate SHA-256 *while* reading the upload stream to avoid reading the file twice (once for hash, once for save).
3.  **Atomic CAS Writes**: Write to `.tmp`, then `os.rename`.
4.  **Locking**: Use `redlock` or a simple DB unique constraint on the `hash` field to handle concurrent uploads of the same asset.
5.  **Chunked Uploads**: For large files (100MB+), consider implementing TUS protocol or simple chunking to avoid memory exhaustion.


