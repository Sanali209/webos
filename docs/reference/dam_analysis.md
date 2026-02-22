# DAM Module Analysis

## 1. How It Works (Architecture Overview)
The Digital Asset Management (DAM) module serves as a **Transparent Indexer** and knowledge base layer over the existing file system. It treats the local disk or NAS as the single source of truth—it does not move, rename, or alter the original files. Instead, it builds a rich metadata graph and search index around them.

**Key Components:**
- **AssetService**: The core registration engine that syncs metadata and manages ingestion.
- **WatcherService**: A watchdog-based synchronizer that listens to file system events (creates, modifies, deletes) to keep the database in sync.
- **Media Processing Pipeline**: An asynchronous TaskIQ-based pipeline that extracts metadata, generates thumbnails, and runs AI enrichments.
- **VectorService**: Integrates with Qdrant for storing and searching vector embeddings (CLIP/BLIP).
- **UnifiedSearchService**: Provides hybrid search capabilities (keyword, vector, and graph-based).

## 2. Data Flow
The ingestion and processing flow is highly asynchronous to ensure non-blocking operations:

1. **Detection**: A file is dropped into a watched directory. The `WatcherService` detects the `FileCreatedEvent`.
2. **Registration**: `AssetService.register_path()` computes a SHA-256 hash, validates the MIME type, and creates a new `Asset` document with a `PROCESSING` status.
3. **Task Queuing**: A background job is dispatched to a Redis queue via TaskIQ (`pipeline_task.kiq(asset_id)`).
4. **Parallel Processing**:
   - **MetadataExtractor**: Extracts EXIF, IPTC, XMP, and geographic data using `pyexiv2`.
   - **ThumbnailGenerator**: Generates web-optimized WebP thumbnails using Pillow and FFmpeg.
   - **AssetDriverManager**: Dispatches format-specific drivers (Image, Video, Audio, Document) to extract dimensions, duration, codecs, etc.
5. **AI Enrichment (Pipeline Orchestrator)**:
   - **BLIP Processor**: Generates natural language captions.
   - **CLIP Processor**: Generates image embeddings.
   - **AutoTagger**: Uses models like SmileWolf for tagging.
   - **MobileNet/YOLO Processor**: Detects specific objects and bounding boxes.
6. **Indexing**: Embeddings are upserted into Qdrant (`VectorService`). Vector relations (Links) are computed to link visually similar assets in the graph.
7. **Ready State**: The asset is marked as `READY` and becomes fully searchable.

## 3. Future Plans for Testing
Based on the DAM Roadmap, the testing strategy is heavily focused on resilience, graceful degradation, and preventing regressions across 10 progressive phases:

### Phase 1-3: Structural & Data Model Integrity
- **Degradation Testing**: Ensure the WebOS boots correctly even if Qdrant is stopped. Verify that invalid asset types or missing services do not crash the application.
- **Isolation Testing**: Verify `OwnedDocument` isolation bounds (e.g., users cannot see each other's albums).

### Phase 4-5: Service & Extraction Resilience
- **Corrupt File Handling**: Ensure corrupted images or videos do not crash the extraction pipeline but safely log errors and mark assets with partial processing statuses.
- **Race Condition Prevention**: Test the `WatcherService`'s debouncing mechanism to handle rapid file copy bursts without duplicating records. Verify the fallback periodic "scavenger" cron job properly reconciles missed file system events.
- **Idempotency**: Ensure that re-ingesting the same file updates records rather than duplicating them.

### Phase 6-7: AI & Vector Infrastructure Pipeline
- **Cold-Start & Missing Models**: Ensure the system gracefully handles missing AI models (e.g., caching `ModelNotAvailableError`) by logging the pipeline error and continuing with generic metadata.
- **Orchestrator Stability**: Verify that if one processor fails, the remaining processors continue executing.

### Phase 8-10: Search, API, & UI End-to-End
- **Search Degradation**: If the Vector Service is down, keyword search via MongoDB text indices must continue to function. If text indices fail, graph search should act as a fallback.
- **Full System Degradation Test**: A comprehensive final test simulating an offline environment by killing Qdrant, disabling the AI engine (`DAM_AI_ENABLED=False`), and removing text indices, to ensure basic CRUD, gallery viewing, and UI overlays remain functional.
