# Digital Asset Management (DAM) Module Design

## 1. Overview
The **DAM Module** acts as a **Transparent Indexer** and "Knowledge Base" layer over your existing file system (NAS/Local). It does **not** move or rename your files. Instead, it indexes them, extracts rich metadata, and builds a graph of relationships, treating the disk as the single source of truth.

## 2. Architecture

> [!IMPORTANT]
> **Phase 0 prerequisite.** The DAM module depends on five improvements to the core framework (`src/core/`). Those changes must land before the DAM module is implemented. See **§9 Framework Integration (Phase 0)** for the full specification.

### 2.1. Module Topology

```
WebOS Core (src/core/)
│
├── hooks.py         ← WebOSHookSpec (pluggy)
│     ├── register_models            → DAM: Asset, Link, Album
│     ├── register_routes            → DAM: FastAPI router
│     ├── register_services      [NEW Phase 0] → DAM wires VectorService, WatcherService, AssetDriverManager
│     ├── on_startup_async       [NEW Phase 0] → DAM starts WatcherService, Qdrant collection bootstrap
│     ├── register_pipeline_processors [NEW Phase 0] → BLIP, CLIP, MobileNet, AutoTagger
│     ├── register_asset_drivers  [NEW Phase 0] → ImageDriver, VideoDriver, UrlDriver …
│     ├── register_vector_definitions [NEW Phase 0] → external models (DINOv2, custom)
│     ├── register_settings          → DAMSettings (watch paths, cache dir, AI flag)
│     └── register_admin_widgets     → DAM stats card
│
├── registry.py      ← ServiceRegistry (type-keyed) + register_named/get_named [NEW Phase 0]
├── config.py        ← Settings + QDRANT_URL, DAM_WATCH_PATHS, DAM_CACHE_DIR [NEW Phase 0]
├── storage.py       ← AFSManager / DataSource Protocol
├── tasks.py         ← Redis ListQueueBroker (TaskIQ)
└── event_bus.py     ← EventBus (in-process pub/sub)

src/modules/dam/
├── hooks.py          ← DAMHooks (implements all hookspecs above)
├── models.py         ← Asset, Link, Album (CoreDocument / OwnedDocument)
├── router.py         ← FastAPI endpoints
├── services/
│   ├── asset_service.py
│   ├── vector_service.py     ← Qdrant async client
│   ├── unified_search.py
│   └── link_manager.py
├── drivers/
│   ├── registry.py           ← AssetDriverRegistry
│   ├── manager.py            ← AssetDriverManager
│   ├── image_driver.py
│   ├── video_driver.py
│   └── url_driver.py
└── processors/
    ├── blip_processor.py
    ├── clip_processor.py
    ├── auto_tagger.py
    └── detection/
        ├── class_hierarchy.py
        └── mobilenet_processor.py
```

### 2.2. Relationship with Storage Module
The `dam` module uses `storage` for **read-only access** to originals and **write access** to the sidecar cache. It never moves or renames source files.

| Concern | Owner |
|---|---|
| Raw I/O, File Listing, URN resolution | `storage` (`AFSManager`) |
| Indexing, Metadata, Thumbnails | `dam` (AssetService) |
| Vector Embeddings (ANN search) | `dam` (VectorService → Qdrant) |
| Background Jobs | Core TaskIQ broker (Redis) |
| File System Events | `dam` (WatcherService → watchdog) |

### 2.3. Data Flow (Ingest → Ready)

```
           File dropped / WatcherService detects
                          │
              AssetService.register_path()
                  (idempotent, MIME detect)
                          │
                   Asset saved (PROCESSING)
                          │
              pipeline_task.kiq(asset_id)    ← TaskIQ worker
                          │
            ┌─────────────┼──────────────────┐
            │             │                  │
     MetadataExtractor  ThumbnailGenerator  AssetDriverManager
     (pyexiv2/ffprobe)  (Pillow/ffmpeg)     └─ dispatch to Driver
            │             │                        │
            └─────────────┴──────────────────────── ▼
                           Asset saved (INDEXING)
                                  │
              ┌────────────────┐  │  ┌──────────────────────┐
              │ BLIP captioning│  │  │ CLIP image embedding  │
              │ (blip_text vec)│  │  │ (clip vec, clip_text) │
              └───────┬────────┘  │  └──────────┬──────────── ┘
                      │           │             │
             AutoTagger (ai_tags) │   MobileNet (detected_objects + mobilenet vec)
                      │           │             │
                      └───────────┴─────────────┘
                                  │
                           Qdrant upsert (named vectors)
                                  │
                         create_vector_relations()
                          (visually_similar_to Links)
                                  │
                       Asset saved (READY) ✓
```

## 3. Data Models

### 3.1. Asset Type Extension Point (Open Registry)

**Problem:** A hardcoded `AssetType` enum prevents modules from defining their own asset types (e.g., a `3d_model` type from a CAD module).

**Solution:** Replace the enum with an open **string key** on the `Asset` model, backed by an `AssetTypeRegistry`. This follows the same pattern as the existing `ServiceRegistry` in `src/core/registry.py`.

```python
# src/modules/dam/type_registry.py

from dataclasses import dataclass, field
from typing import Dict, Optional, Type
from pydantic import BaseModel

@dataclass
class AssetTypeDefinition:
    """
    Descriptor registered by a driver for a specific asset type.
    Modules call AssetTypeRegistry.register() in their on_startup hook.
    """
    key: str                    # Unique string key, e.g. "image", "video", "3d_model"
    label: str                  # Human-readable label for UI
    category: str               # "physical" | "virtual" | "composite"
    icon: str = "description"   # Material icon name for the UI
    # Optional Pydantic schema for the metadata namespace
    metadata_schema: Optional[Type[BaseModel]] = None
    # MIME type prefixes this type handles, e.g. ["image/"]
    mime_prefixes: list[str] = field(default_factory=list)

class AssetTypeRegistry:
    """
    Open registry for asset types. Core types are registered at startup;
    modules register their own types via the `register_asset_types` hook.
    No hardcoded enum — types are plain strings on Asset.asset_type.
    """
    _instance: Optional["AssetTypeRegistry"] = None
    _types: Dict[str, AssetTypeDefinition] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, definition: AssetTypeDefinition) -> None:
        if definition.key in self._types:
            raise ValueError(f"Asset type '{definition.key}' is already registered.")
        self._types[definition.key] = definition

    def get(self, key: str) -> Optional[AssetTypeDefinition]:
        return self._types.get(key)

    def resolve_from_mime(self, mime_type: str) -> str:
        """Auto-detect asset type from MIME type. Falls back to 'other'."""
        for key, defn in self._types.items():
            if any(mime_type.startswith(p) for p in defn.mime_prefixes):
                return key
        return "other"

    def all(self) -> Dict[str, AssetTypeDefinition]:
        return dict(self._types)

asset_type_registry = AssetTypeRegistry()
```

#### Built-in Type Registration (in `dam/hooks.py` → `on_startup`)
```python
# Registered by the DAM module itself on startup:
BUILTIN_TYPES = [
    AssetTypeDefinition("image",       "Image",        "physical", "image",       mime_prefixes=["image/"]),
    AssetTypeDefinition("video",       "Video",        "physical", "videocam",    mime_prefixes=["video/"]),
    AssetTypeDefinition("audio",       "Audio",        "physical", "audiotrack",  mime_prefixes=["audio/"]),
    AssetTypeDefinition("document",    "Document",     "physical", "description", mime_prefixes=["application/pdf", "text/"]),
    AssetTypeDefinition("other",       "Other",        "physical", "insert_drive_file"),
    # Virtual
    AssetTypeDefinition("url",         "Web Bookmark", "virtual",  "link"),
    AssetTypeDefinition("collection",  "Collection",   "virtual",  "folder_special"),
    # Composite
    AssetTypeDefinition("region",      "Image Region", "composite","crop"),
    AssetTypeDefinition("app_package", "App Package",  "composite","apps"),
]
```

#### Pluggy Hook for External Module Registration
```python
# src/core/hooks.py  (add to WebOSHookSpec)
@hookspec
def register_asset_types() -> List[AssetTypeDefinition]:
    """
    Register custom asset types with the DAM AssetTypeRegistry.
    Called during DAM module startup after built-ins are loaded.
    Example: a 3D CAD module returns [AssetTypeDefinition("3d_model", ...)]
    """
```

---

### 3.2. `Asset` Document (CoreDocument)

```python
# src/modules/dam/models.py

class AssetStatus(str, Enum):
    UPLOADING  = "uploading"
    PROCESSING = "processing"
    READY      = "ready"
    MISSING    = "missing"   # FS source no longer found
    ERROR      = "error"

class Asset(CoreDocument, OwnedDocument):
    """Primary entity. asset_type is a registry key string, not an enum."""

    # --- Core ---
    filename:      str
    size:          Optional[int]   = None
    mime_type:     Optional[str]   = None
    # Multi-type: an asset can belong to multiple type keys simultaneously.
    # e.g. ["image", "region"] for a bounding-box crop, ["document", "invoice"] for a typed doc.
    # Primary type is asset_types[0]. Querying uses $in on this list.
    asset_types:   List[str]       = ["other"]
    status:        AssetStatus     = AssetStatus.UPLOADING
    error_message: Optional[str]   = None
    visibility:    str             = "private"

    # --- Storage ---
    storage_urn: str   # e.g. "fs://local/...", "fs://s3/...", "virtual://url/..."

    # --- Fingerprints ---
    hash:  Optional[str] = None   # SHA-256 for deduplication
    phash: Optional[str] = None   # Perceptual hash for visual similarity

    # --- Visuals ---
    thumbnails: Dict[str, str] = {}  # {"small": urn, "medium": urn, "large": urn}
    width:    Optional[int]   = None
    height:   Optional[int]   = None
    duration: Optional[float] = None

    # --- Basic Metadata ---
    title:       Optional[str] = None
    description: Optional[str] = None
    tags:        List[str]     = []  # Manual tags

    # --- AI-Generated Fields ---
    # Populated by the AI pipeline processors (see §4.10–4.12)
    ai_caption:       Optional[str]  = None  # BLIP-generated natural language description
    ai_tags:          List[str]      = []    # Smile/Wolf tagger auto-tags (e.g. "outdoor", "portrait")
    ai_confidence:    Dict[str, float] = {}  # tag → confidence score

    # Object detection results (from MobileNet/YOLO processor)
    detected_objects: List[Dict[str, Any]] = []
    # e.g. [{"class": "animal", "subclass": "dog", "confidence": 0.92,
    #         "bbox": [x1,y1,x2,y2], "model": "mobilenet_v3"}]

    # Vector indexing status: which named Qdrant vectors exist for this asset.
    # {"clip": true, "blip_text": true, "mobilenet": false}
    vectors_indexed:  Dict[str, bool] = {}

    # --- Namespaced Metadata (Schema-on-Read) ---
    metadata: Dict[str, Any] = {}

    version: int = 1

    @property
    def primary_type(self) -> str:
        return self.asset_types[0] if self.asset_types else "other"

    class Settings:
        name = "dam_assets"
        indexes = [
            [("asset_types", 1)],
            [("status", 1)],
            [("hash", 1)],
            [("storage_urn", 1)],
            [("tags", 1)],
            [("ai_tags", 1)],
            [("detected_objects.class", 1)],
            [("detected_objects.subclass", 1)],
            # Full-text index for keyword_channel (UnifiedSearchService)
            [("filename", "text"), ("title", "text"), ("description", "text"),
             ("tags", "text"), ("ai_tags", "text"), ("ai_caption", "text")],
        ]
```

---

### 3.3. `Link` Document (Knowledge Graph Edge)

```python
class Link(CoreDocument):
    """Directed edge in the Knowledge Graph: Source -[relation]-> Target."""
    source_id:   PydanticObjectId
    source_type: str  # "Asset", "User", "Project"
    target_id:   PydanticObjectId
    target_type: str
    relation:    str        # "contains" | "transformed_to" | "visually_similar_to"
    weight:      float = 1.0
    metadata:    Dict[str, Any] = {}

    class Settings:
        name = "dam_links"
        indexes = [
            [("source_id", 1), ("relation", 1)],
            [("target_id", 1), ("relation", 1)],
        ]
```

**Semantic Relation Types:**

| Category     | Relation              | Example                        |
|--------------|-----------------------|--------------------------------|
| Hierarchical | `contains`            | Folder → Asset                 |
| Hierarchical | `includes`            | Album → Asset                  |
| Derivative   | `transformed_to`      | RAW → JPEG                     |
| Derivative   | `extracted_from`      | Text → PDF                     |
| Associative  | `visually_similar_to` | pHash match (weight = score)   |
| Associative  | `depicts`             | Photo → Person tag             |

---

### 3.4. `Album` Document

```python
class Album(CoreDocument, OwnedDocument):
    """Virtual collection. Does not copy files — only references via Links."""
    name:        str
    description: Optional[str] = None
    parent_id:   Optional[PydanticObjectId] = None  # Nested albums
    cover_asset_id: Optional[PydanticObjectId] = None

    class Settings:
        name = "dam_albums"
```

---

### 3.5. Layered Metadata Architecture

| Layer | Storage     | Populated By           | Example Keys                    |
|-------|-------------|------------------------|---------------------------------|
| 1 Core  | Direct fields | System                | `asset_type`, `status`, `hash`  |
| 2 Technical | Direct fields | Pipeline workers  | `width`, `height`, `duration`   |
| 3 Namespaced | `metadata` dict | Drivers & Extractors | `exif`, `iptc`, `xmp`, `geo` |
| 4 Contextual | `Link` collection | Graph service   | `contains`, `transformed_to`    |

**Schema-on-Read pattern** (matching `AssetSDK` style):
```python
def get_metadata(asset: Asset, namespace: str, schema: Type[T]) -> T:
    return schema(**asset.metadata.get(namespace, {}))

# Usage:
exif = get_metadata(asset, "exif", ExifSchema)
geo  = get_metadata(asset, "geo",  GeoSchema)
```

## 4. Components

### 4.1. `AssetService` (The Transparent Indexer)
This service registers existing files and syncs metadata without altering the originals.

#### 4.1.1. Ingestion / Indexing Phase

**A. Physical Files (`register_path`)**:
```python
async def register_path(self, path: Path, owner_id: PydanticObjectId) -> Asset:
    """
    Idempotent — safe to call repeatedly. Updates existing record if
    storage_urn already exists; creates new one otherwise.
    """
    storage_urn = f"fs://local/{path.as_posix()}"
    existing = await Asset.find_one(Asset.storage_urn == storage_urn)

    mime = magic.from_file(str(path), mime=True)          # python-magic singleton
    primary_type = asset_type_registry.resolve_from_mime(mime)

    asset = existing or Asset(
        filename=path.name,
        storage_urn=storage_urn,
        owner_id=owner_id,
        asset_types=[primary_type],   # multi-type list; drivers may append more
        mime_type=mime,
        size=path.stat().st_size,
        status=AssetStatus.PROCESSING,
    )
    await asset.save()
    # Dispatch async pipeline (TaskIQ)
    await pipeline_task.kiq(str(asset.id))
    return asset
```

**B. Virtual Assets (`ingest_virtual`)**:
```python
async def ingest_virtual(self, asset_type: str, data: dict, owner_id) -> Asset:
    asset = Asset(
        filename=data.get("title", asset_type),
        storage_urn=f"virtual://{asset_type}/{uuid4()}",
        owner_id=owner_id,
        asset_types=[asset_type],   # ← multi-type list (Phase 0: no longer a plain string)
        status=AssetStatus.PROCESSING,
        metadata={asset_type: data},
    )
    await asset.save()
    await pipeline_task.kiq(str(asset.id))
    return asset
```

#### 4.1.2. Analysis Phase (Async — TaskIQ Worker)

| Step | Tool / Library | Output |
|------|---------------|--------|
| MIME validation | `python-magic` (singleton) | `asset.mime_type` |
| SHA-256 hash | `hashlib` (chunked) | `asset.hash` |
| Perceptual hash | `imagehash` (pHash) | `asset.phash` |
| Image metadata | `pyexiv2` | `asset.metadata["exif"]`, `["iptc"]`, `["xmp"]` |
| Video metadata | `ffprobe` (subprocess) | `asset.metadata["video"]` |
| Dimensions | `Pillow` / `ffprobe` | `asset.width`, `asset.height` |
| Thumbnail gen | `Pillow` + `ffmpeg` | `asset.thumbnails` |

#### 4.1.3. Derivative Generation (Async)
- **Thumbnails**: Pyramid generation → `small` (200px) / `medium` (800px) / `large` (1920px).
- **Transcoding**: TIFF→WebP, MOV→MP4 for web delivery.
- **OCR**: Tesseract text extraction for documents → `asset.metadata["ocr"]`.

---

### 4.2. `ThumbnailGenerator`

```python
class ThumbnailGenerator:
    SIZES = {"small": 200, "medium": 800, "large": 1920}

    @property
    def cache_root(self) -> Path:
        # Reads from settings so DAM_CACHE_DIR env var is respected.
        return Path(settings.DAM_CACHE_DIR)

    async def generate(self, asset: Asset) -> Dict[str, str]:
        path = self._resolve_path(asset.storage_urn)
        thumbs: Dict[str, str] = {}
        for name, px in self.SIZES.items():
            out = self.cache_root / asset.hash[:2] / asset.hash / f"{name}.webp"
            out.parent.mkdir(parents=True, exist_ok=True)
            if "video" in asset.asset_types:   # ← use multi-type list (Phase 0)
                await self._extract_frame(path, out, px)
            else:
                await asyncio.to_thread(self._resize_image, path, out, px)
            thumbs[name] = f"fs://cache/{out.relative_to(self.cache_root)}"
        return thumbs

    def _resize_image(self, src: Path, dst: Path, max_px: int):
        with Image.open(src) as img:
            img.thumbnail((max_px, max_px), Image.LANCZOS)
            img.save(dst, "WEBP", quality=85)
```

> **Storage**: `data/dam_cache/{hash[:2]}/{hash}/{size}.webp` — sharded by first 2 hash chars to avoid filesystem inode limits on large collections.

---

### 4.3. `MetadataExtractor` (pyexiv2-based)

**Why pyexiv2?** It is a Python 3 binding to the battle-tested **Exiv2** C++ library. It reads/writes **EXIF, IPTC, XMP, and ICC** in one pass from a single file handle — no subprocess overhead unlike ExifTool wrappers.

> ⚠️ **Thread Safety**: `pyexiv2.Image` objects are **not thread-safe**. Each worker thread must open its own `Image` instance and close it with `.close()` when done.

```python
# src/modules/dam/services/metadata_extractor.py
import pyexiv2
from pathlib import Path
from typing import Dict, Any

class MetadataExtractor:
    """
    Extracts EXIF / IPTC / XMP metadata using pyexiv2.
    Runs in a thread pool (asyncio.to_thread) — never in the event loop.
    Outputs are namespaced dicts ready to store in Asset.metadata.
    """

    SUPPORTED_MIME_PREFIXES = ["image/jpeg", "image/png", "image/tiff",
                                "image/webp", "image/heic"]

    def extract(self, path: Path) -> Dict[str, Any]:
        """Returns {'exif': {...}, 'iptc': {...}, 'xmp': {...}}"""
        result: Dict[str, Any] = {}
        img = pyexiv2.Image(str(path))
        try:
            result["exif"] = self._clean(img.read_exif())
            result["iptc"] = self._clean(img.read_iptc())
            result["xmp"]  = self._clean(img.read_xmp())
            result["geo"]  = self._extract_geo(result["exif"])
        except Exception as e:
            logger.warning(f"pyexiv2 failed for {path}: {e}")
        finally:
            img.close()  # mandatory — releases C++ resources
        return result

    def _clean(self, raw: dict) -> dict:
        """Strip namespace prefixes (e.g. 'Exif.Image.Make' → 'Make')."""
        return {k.split(".")[-1]: v for k, v in raw.items() if v is not None}

    def _extract_geo(self, exif: dict) -> dict:
        """Parse GPSLatitude / GPSLongitude from cleaned EXIF dict."""
        try:
            lat = self._dms_to_decimal(exif.get("GPSLatitude"), exif.get("GPSLatitudeRef"))
            lon = self._dms_to_decimal(exif.get("GPSLongitude"), exif.get("GPSLongitudeRef"))
            if lat and lon:
                return {"lat": lat, "lon": lon}
        except Exception:
            pass
        return {}

    def _dms_to_decimal(self, dms_str: str, ref: str) -> float | None:
        if not dms_str or not ref:
            return None
        # pyexiv2 returns rational strings: "51/1 30/1 0/1"
        parts = [eval(p) for p in dms_str.split()]
        decimal = parts[0] + parts[1] / 60 + parts[2] / 3600
        if ref in ("S", "W"):
            decimal = -decimal
        return round(decimal, 7)
```

**Pydantic Output Schemas (Schema-on-Read)**:
```python
class ExifSchema(BaseModel):
    Make:             Optional[str] = None
    Model:            Optional[str] = None
    DateTimeOriginal: Optional[str] = None
    ExposureTime:     Optional[str] = None
    FNumber:          Optional[str] = None
    ISOSpeedRatings:  Optional[int] = None
    LensModel:        Optional[str] = None

class GeoSchema(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None

class IptcSchema(BaseModel):
    Keywords:        List[str] = []
    CaptionAbstract: Optional[str] = None
    Byline:          Optional[str] = None
    CopyrightNotice: Optional[str] = None
```

**Fallback Chain** (when pyexiv2 fails — e.g., unsupported format):
```
pyexiv2  →  Pillow._getexif()  →  ffprobe (video)  →  {} (empty, no error)
```

**Async wrapper** (called from TaskIQ worker):
```python
async def extract_async(self, path: Path) -> Dict[str, Any]:
    return await asyncio.to_thread(self.extract, path)
```

### 4.4. Media Processing Pipeline (Async & Extensible)
A pluggable system for background asset processing.

- **Architecture**:
    - **`MediaProcessor` Protocol**: Interface for plugins to implement (`process(asset_id: PydanticObjectId) -> None`).
    - **`PipelineService`**: Registry that manages and executes processors.
    - **TaskIQ Integration**: All processing happens in background workers to keep the UI responsive.
- **Workflow**:
    1.  User Uploads File -> `AssetService` saves original.
    2.  `AssetService` triggers `pipeline_task.kiq(asset_id)`.
    3.  Worker iterates through registered processors (Metadata, Thumbnails, AI, etc.).
- **Extensibility**:
    - Modules can register processors via hook: `@hookspec def register_media_processors()`.
- **Planned Processors**:
    - **OCR**: Text recognition for scanned documents (e.g., Tesseract).
    - **AI Tagging**: Object detection/classification (e.g., CLIP, TensorFlow) to auto-tag images.
    - **Virtual Processors**:
        - **Web Scraper** (URL): Fetches title, favicon, and generates Screenshot (Child Asset).
        - **Collection Preview** (Album): Generates collage from first 4 assets.

### 4.5. `WatcherService` (The Core FS Synchronizer)

Since the **file system is the source of truth**, the `WatcherService` is the bridge keeping MongoDB in sync when files change outside the application.

#### Architecture: Dual-Mode Sync

```
                 ┌──────────────────────┐
  File System    │  watchdog Observer   │  (event-driven, real-time)
  ─────────────► │  DAMEventHandler     │──────────► asyncio.Queue
                 └──────────────────────┘                │
                                                         ▼
                                               fsync_worker coroutine
                                               (debounce + dispatch)
                                                         │
                                                         ▼
                                                   AssetService
                                                         │
                 ┌──────────────────────┐               │
  TaskIQ         │ scavenger_task (cron)│◄──────────────┘
  (periodic)     │ every 15 min         │  catches missed events
                 └──────────────────────┘  (app was down, NAS mount)
```

#### `DAMEventHandler` — watchdog Handler

```python
# src/modules/dam/services/watcher_service.py
import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler, FileCreatedEvent,
    FileMovedEvent, FileDeletedEvent, FileModifiedEvent,
    PatternMatchingEventHandler,
)

IGNORED_PATTERNS = ["*.tmp", "*.part", ".DS_Store", "Thumbs.db", "~*"]
WATCHED_EXTENSIONS = ["*.jpg", "*.jpeg", "*.png", "*.tiff", "*.webp",
                       "*.mp4", "*.mov", "*.pdf", "*.mp3", "*.wav"]

class DAMEventHandler(PatternMatchingEventHandler):
    """
    Watchdog handler. Puts events on an asyncio.Queue —
    never calls I/O directly to stay non-blocking.
    """
    def __init__(self, queue: asyncio.Queue):
        super().__init__(
            patterns=WATCHED_EXTENSIONS,
            ignore_patterns=IGNORED_PATTERNS,
            ignore_directories=False,
            case_sensitive=False,
        )
        self._queue = queue
        self._loop = asyncio.get_event_loop()

    def _put(self, event_type: str, **kwargs):
        self._loop.call_soon_threadsafe(
            self._queue.put_nowait, {"type": event_type, **kwargs}
        )

    def on_created(self, event: FileCreatedEvent):
        self._put("created", path=event.src_path)

    def on_deleted(self, event: FileDeletedEvent):
        self._put("deleted", path=event.src_path)

    def on_moved(self, event: FileMovedEvent):
        self._put("moved", src=event.src_path, dst=event.dest_path)

    def on_modified(self, event: FileModifiedEvent):
        self._put("modified", path=event.src_path)
```

#### `WatcherService` — Lifecycle & Debounce

```python
class WatcherService:
    """
    Lifecycle: started via on_startup pluggy hook.
    Manages multiple watched paths (NAS mounts, local dirs).
    """
    DEBOUNCE_SECONDS = 2.0   # coalesce rapid bursts (e.g., copy operations)

    def __init__(self, asset_service: AssetService):
        self._asset_service = asset_service
        self._queue: asyncio.Queue = asyncio.Queue()
        self._observer = Observer()
        self._pending: dict[str, asyncio.TimerHandle] = {}  # debounce registry
        self._watched_paths: list[Path] = []

    def add_watch(self, path: Path, recursive: bool = True):
        """Register a path to monitor. Can be called multiple times."""
        handler = DAMEventHandler(self._queue)
        self._observer.schedule(handler, str(path), recursive=recursive)
        self._watched_paths.append(path)
        logger.info(f"WatcherService: watching {path} (recursive={recursive})")

    async def start(self):
        self._observer.start()
        asyncio.create_task(self._fsync_worker())
        logger.info("WatcherService started.")

    async def stop(self):
        self._observer.stop()
        self._observer.join()

    async def _fsync_worker(self):
        """Consumes events from queue with debouncing."""
        loop = asyncio.get_running_loop()
        while True:
            event = await self._queue.get()
            key = event.get("path") or event.get("src")

            # Cancel existing timer for same path (debounce)
            if key in self._pending:
                self._pending[key].cancel()

            handle = loop.call_later(
                self.DEBOUNCE_SECONDS,
                lambda e=event: asyncio.create_task(self._dispatch(e))
            )
            self._pending[key] = handle

    async def _dispatch(self, event: dict):
        """Route event to the correct AssetService method."""
        owner_id = await self._resolve_owner(event.get("path"))
        try:
            match event["type"]:
                case "created":
                    await self._asset_service.register_path(
                        Path(event["path"]), owner_id
                    )
                case "modified":
                    await self._asset_service.refresh_asset(
                        Path(event["path"])  # re-hash + re-extract metadata
                    )
                case "moved":
                    await self._asset_service.update_storage_urn(
                        old_path=Path(event["src"]),
                        new_path=Path(event["dst"]),
                    )
                case "deleted":
                    await self._asset_service.mark_missing(Path(event["path"]))
        except Exception as e:
            logger.error(f"WatcherService dispatch error for {event}: {e}")

    async def _resolve_owner(self, path: str) -> PydanticObjectId:
        """Map watched path prefix to system owner ID (configurable)."""
        # Default: use configured system_owner_id from DAM settings
        return settings.DAM_SYSTEM_OWNER_ID
```

#### Periodic Scavenger Task (TaskIQ Cron)

Catches events missed while the app was offline (e.g., NAS remounted).

```python
# src/modules/dam/tasks.py
from taskiq_redis import ListQueueBroker
from src.core.tasks import broker

@broker.task(schedule=[{"cron": "*/15 * * * *"}])   # every 15 minutes
async def scavenger_task():
    """
    1. Walk all watched paths → register new files not yet in DB.
    2. Query all PHYSICAL assets → verify file still exists → mark MISSING if not.
    3. Query MISSING assets   → check if file reappeared → re-register.
    """
    watcher_service = ServiceRegistry.get(WatcherService)
    asset_service   = ServiceRegistry.get(AssetService)

    # Phase 1: Discover new files
    for watch_path in watcher_service.watched_paths:
        async for path in _walk_async(watch_path):
            if not await Asset.find_one(Asset.storage_urn == f"fs://local/{path.as_posix()}"):
                await asset_service.register_path(path, owner_id=settings.DAM_SYSTEM_OWNER_ID)

    # Phase 2: Verify existing PHYSICAL assets
    async for asset in Asset.find(Asset.status != AssetStatus.MISSING):
        path = _urn_to_path(asset.storage_urn)
        if path and not path.exists():
            asset.status = AssetStatus.MISSING
            await asset.save()
            logger.warning(f"Asset {asset.id} marked MISSING: {path}")

    # Phase 3: Re-discover previously MISSING assets
    async for asset in Asset.find(Asset.status == AssetStatus.MISSING):
        path = _urn_to_path(asset.storage_urn)
        if path and path.exists():
            await asset_service.refresh_asset(path)
```

#### Startup Integration (Phase 0 `on_startup_async` hook)

The `WatcherService.start()` is async (it schedules a watchdog thread + `asyncio.create_task`). It **must** run in `on_startup_async`, not `on_startup`. The wiring of the service itself (`add_watch`) happens in `register_services` (also Phase 0), so `on_startup_async` only needs to call `start()`.

```python
# src/modules/dam/hooks.py  (already shown in §9.6 — reproduced here for context)
@hookimpl
def register_services(self):
    # ... (VectorService, drivers) ...
    if settings.DAM_WATCH_PATHS:
        asset_svc = ServiceRegistry.get(AssetService)
        watcher = WatcherService(asset_svc)
        for path_str in settings.DAM_WATCH_PATHS:
            watcher.add_watch(Path(path_str))
        ServiceRegistry.register(WatcherService, watcher)  # register BEFORE async start

@hookimpl
async def on_startup_async(self):              # ← async hook, awaited by lifespan
    watcher = ServiceRegistry.get_named_optional(WatcherService.__name__)
    vs = ServiceRegistry.get(VectorService)
    await vs.ensure_collection()               # Qdrant bootstrap
    if watcher:
        await watcher.start()                  # starts observer thread + fsync coroutine
```

> [!NOTE]
> `asyncio.create_task(watcher.start())` (the old pattern) is **wrong** — it fires and forgets without error checking. The `on_startup_async` hook is awaited, so errors surface correctly.

#### File Completeness Check (Anti-Race)

Before processing a `created`/`modified` event, verify the file is **fully written**:

```python
async def _wait_for_stable_size(path: Path, interval=0.5, retries=6) -> bool:
    """Return True when file size stops changing (write complete)."""
    prev_size = -1
    for _ in range(retries):
        curr_size = path.stat().st_size if path.exists() else -1
        if curr_size == prev_size and curr_size >= 0:
            return True
        prev_size = curr_size
        await asyncio.sleep(interval)
    return False
```

---

### 4.6. Integrity & Deduplication (Logical)
-   **Logical Dedup**: SHA-256 is used to *find* duplicates, not to store them.
    -   UI warns: "This file also exists in /backup/photos/".
-   **Bitrot Check**: Background task verifying file hash against DB.

### 4.7. `LinkManager` (Graph Service)
Manages the connections between entities.

- **Core Operations**:
    - `link(source, target, relation)`: Create edge.
    - `get_neighbors(node_id, relation_type)`: Traversing.
    - `shortest_path(start, end)`: Provenance tracking.
    - `impact_analysis(node_id)`: Find dependent nodes (incoming edges).
- **Automation**:
    - **Propagation**: Propagate tags/permissions down hierarchical edges.
    - **Integrity**: `on_delete` hooks to clean up orphaned links.

### 4.8. Asset Drivers (The "Brain" of the Asset)

Drivers replace hardcoded `if asset_type == "image"` branches. They implement the **Strategy Pattern** — each asset type has an associated driver that owns its entire lifecycle.

#### Protocol Definition

```python
# src/modules/dam/drivers/base.py
from typing import Protocol, runtime_checkable, Optional, Dict, Any
from pathlib import Path

@runtime_checkable
class AssetDriver(Protocol):
    """
    Strategy interface that each asset type implements.
    Drivers are registered against string type keys in AssetTypeRegistry —
    no hardcoded enum anywhere in this interface.

    All methods are *optional* — drivers only implement what they support.
    Default no-op implementations are provided by BaseAssetDriver.
    """

    @property
    def asset_type_key(self) -> str:
        """The string key this driver handles, e.g. 'image', 'video'."""
        ...

    async def on_ingest(self, asset: "Asset", source: Path | dict) -> None:
        """
        Called once, right after the Asset record is first persisted.
        Physical drivers: run MIME check, hash, initial metadata extraction.
        Virtual drivers: fetch remote data, resolve canonical URN.
        """
        ...

    async def generate_thumbnail(self, asset: "Asset") -> Dict[str, str]:
        """
        Return {'small': urn, 'medium': urn, 'large': urn}.
        Drives the ThumbnailGenerator — drivers decide *how* to preview.
        Image: crop + resize. Video: extract frame. URL: screenshot. 
        """
        ...

    async def extract_metadata(self, asset: "Asset") -> Dict[str, Any]:
        """
        Return namespaced metadata dict.
        E.g. {'exif': {...}, 'geo': {...}} for images.
        Result is merged into asset.metadata by AssetService.
        """
        ...

    def get_ui_actions(self, asset: "Asset") -> list[dict]:
        """
        Return list of context-menu actions for this type.
        {'label': 'Edit in Photopea', 'icon': 'edit', 'handler': 'dam.open_editor'}
        """
        return []
```

#### `BaseAssetDriver` — Default No-op Implementation

```python
class BaseAssetDriver:
    """Concrete base — override only what the type needs."""
    asset_type_key: str = "other"

    async def on_ingest(self, asset, source): pass
    async def generate_thumbnail(self, asset) -> Dict[str, str]: return {}
    async def extract_metadata(self, asset) -> Dict[str, Any]: return {}
    def get_ui_actions(self, asset) -> list[dict]: return []
```

#### `AssetDriverRegistry` — Open Registry

```python
# src/modules/dam/drivers/registry.py
from typing import Dict, Optional

class AssetDriverRegistry:
    """
    Maps asset_type_key strings to driver instances.
    Follows same singleton pattern as ServiceRegistry in src/core/registry.py.
    """
    _instance: Optional["AssetDriverRegistry"] = None
    _drivers: Dict[str, "AssetDriver"] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, driver: "AssetDriver") -> None:
        key = driver.asset_type_key
        if key in self._drivers:
            logger.warning(f"Driver for '{key}' overridden by {type(driver).__name__}")
        self._drivers[key] = driver
        logger.debug(f"AssetDriver registered: {key} → {type(driver).__name__}")

    def get(self, asset_type_key: str) -> "AssetDriver":
        return self._drivers.get(asset_type_key, self._drivers.get("other"))

    def all(self) -> Dict[str, "AssetDriver"]:
        return dict(self._drivers)

driver_registry = AssetDriverRegistry()
```

#### Pluggy Hook for External Driver Registration

```python
# src/core/hooks.py  (add to WebOSHookSpec)
@hookspec
def register_asset_drivers() -> List[AssetDriver]:
    """
    Register asset drivers with the DAM AssetDriverRegistry.
    Called during DAM module startup after built-in drivers are loaded.
    Example: a Video module returns [VideoDriver(), HlsDriver()]
    """
```

#### Concrete Driver Examples

**`ImageDriver`**:
```python
class ImageDriver(BaseAssetDriver):
    asset_type_key = "image"

    async def extract_metadata(self, asset: Asset) -> Dict[str, Any]:
        path = _urn_to_path(asset.storage_urn)
        extractor = MetadataExtractor()
        return await extractor.extract_async(path)  # pyexiv2 → exif, iptc, xmp, geo

    async def generate_thumbnail(self, asset: Asset) -> Dict[str, str]:
        return await ThumbnailGenerator().generate(asset)

    def get_ui_actions(self, asset: Asset) -> list[dict]:
        return [
            {"label": "Open full size", "icon": "open_in_full", "handler": "dam.open_lightbox"},
            {"label": "Show on map",    "icon": "map",          "handler": "dam.open_geo_view",
             "condition": lambda a: bool(a.metadata.get("geo"))},
        ]
```

**`VideoDriver`**:
```python
class VideoDriver(BaseAssetDriver):
    asset_type_key = "video"

    async def extract_metadata(self, asset: Asset) -> Dict[str, Any]:
        path = _urn_to_path(asset.storage_urn)
        probe = await asyncio.to_thread(ffmpeg.probe, str(path))
        stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
        return {"video": {
            "codec": stream.get("codec_name"),
            "width": stream.get("width"),
            "height": stream.get("height"),
            "duration": float(probe["format"].get("duration", 0)),
            "bitrate": int(probe["format"].get("bit_rate", 0)),
        }}

    async def generate_thumbnail(self, asset: Asset) -> Dict[str, str]:
        # Extract frame at 10% of duration
        return await ThumbnailGenerator().generate(asset)
```

**`UrlDriver`** (Virtual):
```python
class UrlDriver(BaseAssetDriver):
    asset_type_key = "url"

    async def on_ingest(self, asset: Asset, source: dict) -> None:
        # source = {"url": "https://...", "title": "...", "description": "..."}
        asset.title = source.get("title")
        asset.metadata["url"] = source
        await asset.save()
        await screenshot_task.kiq(str(asset.id))  # TaskIQ: generate screenshot

    async def generate_thumbnail(self, asset: Asset) -> Dict[str, str]:
        # Returns screenshot URN generated by screenshot_task
        return asset.thumbnails  # Populated by the background task
```

---

### 4.9. `AssetDriverManager` — Pipeline Orchestrator

The `AssetDriverManager` is the **single entry point** `AssetService` calls for all type-specific processing. It replaces the old hardcoded dispatch.

```python
# src/modules/dam/drivers/manager.py
class AssetDriverManager:
    """
    Orchestrates the full processing pipeline for an asset
    by delegating to the registered driver for its type.
    Called from the TaskIQ pipeline_task worker.
    """
    def __init__(self, registry: AssetDriverRegistry):
        self._registry = registry

    async def process(self, asset: Asset) -> None:
        # Use primary_type (asset_types[0]) for driver dispatch — Phase 0 multi-type field
        driver = self._registry.get(asset.primary_type)
        logger.info(f"Processing asset {asset.id} with {type(driver).__name__}")
        try:
            # Step 1: Extract metadata
            meta = await driver.extract_metadata(asset)
            asset.metadata.update(meta)

            # Step 2: Generate thumbnails
            thumbs = await driver.generate_thumbnail(asset)
            if thumbs:
                asset.thumbnails = thumbs

            # Step 3: Populate visual dimensions from metadata
            if "exif" in meta or "video" in meta:
                _apply_dimensions(asset, meta)

            asset.status = AssetStatus.READY
        except Exception as e:
            asset.status = AssetStatus.ERROR
            asset.error_message = str(e)
            logger.error(f"Pipeline failed for asset {asset.id}: {e}")
        finally:
            await asset.save()

def _apply_dimensions(asset: Asset, meta: dict):
    if "video" in meta:
        asset.width    = meta["video"].get("width")
        asset.height   = meta["video"].get("height")
        asset.duration = meta["video"].get("duration")
    elif "exif" in meta:
        # Pillow reads dimensions reliably; fallback from EXIF
        pass  # ThumbnailGenerator sets these during resize
```

## 5. AI Pipeline & Vector Intelligence

---

### 5.1. `VectorService` — Qdrant Multi-Vector Store

**Architecture Decision:** Qdrant is used as the vector store, separate from MongoDB. MongoDB stores structured asset metadata; Qdrant stores dense embeddings per asset enabling sub-millisecond ANN (Approximate Nearest Neighbor) searches.

**Key Qdrant feature used:** **Named Vectors** — a single Qdrant point (identified by asset MongoDB `_id`) stores multiple vectors of different types and dimensions in one collection, avoiding the overhead of managing separate collections per model.

#### Qdrant Collection Schema

```python
# src/modules/dam/services/vector_service.py
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance, VectorParams, NamedVector,
    PointStruct, Filter, FieldCondition, MatchValue
)

VECTOR_DEFINITIONS = {
    # Model          dim    distance    purpose
    "clip":        (512,   Distance.COSINE),  # CLIP ViT-B/32 image embedding
    "clip_text":   (512,   Distance.COSINE),  # CLIP text embedding for cross-modal search
    "blip_text":   (768,   Distance.COSINE),  # BLIP caption embedding (sentence-transformers)
    "mobilenet":   (1280,  Distance.COSINE),  # MobileNetV3-Large feature vector
    "phash_vec":   (64,    Distance.EUCLID),  # pHash as float vector for near-duplicate search
}

DAM_COLLECTION = "dam_assets"

class VectorService:
    """
    Manages the DAM Qdrant collection and provides upsert / search ops.
    One Qdrant point per Asset; multiple named vectors per point.
    """
    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def ensure_collection(self):
        """Idempotent — creates collection if not exists."""
        existing = {c.name for c in (await self.client.get_collections()).collections}
        if DAM_COLLECTION not in existing:
            await self.client.create_collection(
                collection_name=DAM_COLLECTION,
                vectors_config={
                    name: VectorParams(size=dim, distance=dist)
                    for name, (dim, dist) in VECTOR_DEFINITIONS.items()
                },
            )

    async def upsert_vector(
        self, asset_id: str, vector_name: str, vector: list[float], payload: dict = {}
    ):
        """
        Upsert a single named vector for an asset.
        Other named vectors on this point are NOT overwritten.
        """
        await self.client.upsert(
            collection_name=DAM_COLLECTION,
            points=[PointStruct(
                id=asset_id,   # MongoDB _id string → Qdrant UUID
                vectors={vector_name: vector},
                payload=payload,
            )],
        )

    async def search(
        self,
        vector_name: str,
        query_vector: list[float],
        limit: int = 20,
        filters: dict | None = None,
    ) -> list[dict]:
        """ANN search on a specific named vector."""
        qdrant_filter = self._build_filter(filters) if filters else None
        results = await self.client.search(
            collection_name=DAM_COLLECTION,
            query_vector=NamedVector(name=vector_name, vector=query_vector),
            limit=limit,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        return [{"asset_id": r.id, "score": r.score, **r.payload} for r in results]

    def _build_filter(self, filters: dict) -> Filter:
        conditions = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in filters.items()
        ]
        return Filter(must=conditions)
```

#### Vector Registry (Extension Point)

External modules can register additional vector types:

```python
@hookspec
def register_vector_definitions() -> Dict[str, Tuple[int, Distance]]:
    """
    Register additional Qdrant named vectors.
    Example: {"dino_v2": (1536, Distance.COSINE)}
    Called during DAM startup; VectorService adds these to the collection.
    """
```

---

### 5.2. `BLIPCaptioningProcessor` — Auto Description Generation

**Model:** `Salesforce/blip-image-captioning-large` via HuggingFace Transformers.
**Output:** Natural language caption stored in `asset.ai_caption` + a BLIP text embedding stored as `blip_text` vector in Qdrant.

#### Implementation

```python
# src/modules/dam/processors/blip_processor.py
from transformers import BlipProcessor, BlipForConditionalGeneration
from sentence_transformers import SentenceTransformer
from PIL import Image
import torch, asyncio

class BLIPCaptioningProcessor:  # ← Pipeline processor, NOT an AssetDriver — removed wrong base class
    """
    Pipeline processor: runs BLIP captioning on image assets.
    Also embeds the generated caption with sentence-transformers
    and stores it as 'blip_text' named vector in Qdrant.
    """
    _blip_processor = None
    _blip_model = None
    _embedder = None

    @classmethod
    def _load(cls):
        if cls._blip_model is None:
            cls._blip_processor = BlipProcessor.from_pretrained(
                "Salesforce/blip-image-captioning-large"
            )
            cls._blip_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-large"
            ).eval()
            cls._embedder = SentenceTransformer("all-mpnet-base-v2")  # 768-dim

    def caption_and_embed(self, path: Path) -> tuple[str, list[float]]:
        self._load()
        img = Image.open(path).convert("RGB")
        inputs = self._blip_processor(img, return_tensors="pt")
        with torch.no_grad():
            out = self._blip_model.generate(**inputs, max_new_tokens=60)
        caption = self._blip_processor.decode(out[0], skip_special_tokens=True)
        embedding = self._embedder.encode(caption).tolist()   # 768-dim
        return caption, embedding

    async def process(self, asset: Asset, vector_service: VectorService) -> None:
        if "image" not in asset.asset_types:
            return
        path = _urn_to_path(asset.storage_urn)
        caption, embedding = await asyncio.to_thread(self.caption_and_embed, path)

        asset.ai_caption = caption
        await asset.save()

        await vector_service.upsert_vector(
            asset_id=str(asset.id),
            vector_name="blip_text",
            vector=embedding,
            payload={"caption": caption},
        )
        asset.vectors_indexed["blip_text"] = True
        await asset.save()
```

---

### 5.3. `CLIPEmbeddingProcessor` — Visual & Cross-Modal Embeddings

**Model:** `openai/clip-vit-base-patch32` (512-dim). Stores two named vectors:
- `clip` — image embedding (for image-to-image similarity)
- `clip_text` — text embedding (for text-to-image semantic search)

```python
# src/modules/dam/processors/clip_processor.py
import open_clip
from PIL import Image
import torch, asyncio

class CLIPEmbeddingProcessor:
    _model = _preprocess = _tokenizer = None

    @classmethod
    def _load(cls):
        if cls._model is None:
            cls._model, _, cls._preprocess = open_clip.create_model_and_transforms(
                "ViT-B-32", pretrained="openai"
            )
            cls._tokenizer = open_clip.get_tokenizer("ViT-B-32")
            cls._model.eval()

    def embed_image(self, path: Path) -> list[float]:
        self._load()
        img = self._preprocess(Image.open(path).convert("RGB")).unsqueeze(0)
        with torch.no_grad():
            feat = self._model.encode_image(img)
            feat /= feat.norm(dim=-1, keepdim=True)
        return feat[0].tolist()   # 512-dim

    def embed_text(self, text: str) -> list[float]:
        self._load()
        tokens = self._tokenizer([text])
        with torch.no_grad():
            feat = self._model.encode_text(tokens)
            feat /= feat.norm(dim=-1, keepdim=True)
        return feat[0].tolist()   # 512-dim

    async def process(self, asset: Asset, vector_service: VectorService) -> None:
        if "image" not in asset.asset_types:
            return
        path = _urn_to_path(asset.storage_urn)
        img_vec = await asyncio.to_thread(self.embed_image, path)
        await vector_service.upsert_vector(str(asset.id), "clip", img_vec)
        asset.vectors_indexed["clip"] = True

        # If BLIP caption was already generated, also encode text side
        if asset.ai_caption:
            txt_vec = await asyncio.to_thread(self.embed_text, asset.ai_caption)
            await vector_service.upsert_vector(str(asset.id), "clip_text", txt_vec)
            asset.vectors_indexed["clip_text"] = True

        await asset.save()
```

---

### 5.4. `AutoTaggerProcessor` — Smile/Wolf Tagger

**Purpose:** Hierarchical multi-label image classification. Tags like `"outdoor"`, `"portrait"`, `"landscape"` are written to `asset.ai_tags` with `asset.ai_confidence` scores.

```python
# src/modules/dam/processors/auto_tagger.py
from PIL import Image
import torch, asyncio
from typing import Protocol

class AutoTaggerBackend(Protocol):
    """
    Extension point: any tagger backend can be plugged in.
    The Smile/Wolf tagger is the default implementation.
    Register via hookspec `register_auto_tagger_backend`.
    """
    def predict(self, image: Image.Image) -> Dict[str, float]:
        """Returns {tag: confidence_score} dict."""
        ...

class SmileWolfTagger(AutoTaggerBackend):
    """
    Default backend using the WD-1.4 Tagger V2 model
    (SmilingWolf/wd-v1-4-moat-tagger-v2 on HuggingFace).
    Provides anime/general tags with confidence scores.
    """
    _model = _transform = _labels = None

    # Threshold read from settings so DAM_TAGGER_THRESHOLD env var is respected (default 0.35)
    @property
    def THRESHOLD(self) -> float:
        return settings.DAM_TAGGER_THRESHOLD

    @classmethod
    def _load(cls):
        if cls._model is None:
            from huggingface_hub import hf_hub_download
            import onnxruntime as ort
            import pandas as pd
            model_path = hf_hub_download(
                "SmilingWolf/wd-v1-4-moat-tagger-v2", filename="model.onnx"
            )
            labels_path = hf_hub_download(
                "SmilingWolf/wd-v1-4-moat-tagger-v2", filename="selected_tags.csv"
            )
            cls._model = ort.InferenceSession(model_path)
            cls._labels = pd.read_csv(labels_path)["name"].tolist()

    def predict(self, image: Image.Image) -> Dict[str, float]:
        self._load()
        import numpy as np
        img = image.convert("RGB").resize((448, 448))
        arr = np.array(img, dtype=np.float32)[np.newaxis]
        probs = self._model.run(None, {"input_1": arr})[0][0]
        return {
            label: float(score)
            for label, score in zip(self._labels, probs)
            if score >= self.THRESHOLD
        }

class AutoTaggerProcessor:
    def __init__(self, backend: AutoTaggerBackend = None):
        self._backend = backend or SmileWolfTagger()

    async def process(self, asset: Asset) -> None:
        if "image" not in asset.asset_types:
            return
        path = _urn_to_path(asset.storage_urn)
        img = Image.open(path).convert("RGB")
        raw = await asyncio.to_thread(self._backend.predict, img)

        asset.ai_tags       = list(raw.keys())
        asset.ai_confidence = raw
        # Merge AI tags into searchable unified tags
        asset.tags = list(set(asset.tags + asset.ai_tags))
        await asset.save()
```

**Extension Point Hook:**
```python
@hookspec
def register_auto_tagger_backend() -> AutoTaggerBackend:
    """
    Replace or augment the default SmileWolfTagger.
    Example: a fashion module returns a domain-specific CLIP-based tagger.
    """
```

---

### 5.5. `ObjectDetectionProcessor` — MobileNet with Class Hierarchy

**Model:** MobileNetV3 SSD (TensorFlow Lite / TorchVision). Outputs bounding boxes with hierarchical class/subclass labels.

#### Detection Class Hierarchy

```python
# src/modules/dam/processors/detection/class_hierarchy.py

@dataclass
class DetectionClass:
    """
    Represents one node in the detection class hierarchy.
    Classes are registered via hookspec — not hardcoded.
    """
    key:       str                          # e.g. "animal"
    label:     str                          # e.g. "Animal"
    parent:    Optional[str] = None         # parent key; None = root class
    coco_ids:  List[int]     = field(default_factory=list)  # COCO label IDs mapped here

class DetectionClassRegistry:
    """
    Open registry for detection class hierarchy.
    Built-in classes cover COCO 80 dataset; modules extend for domain classes.
    """
    _tree: Dict[str, DetectionClass] = {}

    def register(self, cls: DetectionClass):
        self._tree[cls.key] = cls

    def resolve(self, coco_label: str) -> tuple[str, str]:
        """Map a raw COCO label to (class, subclass) keys."""
        for cls in self._tree.values():
            if coco_label in (cls.label, cls.key):
                parent = self._tree.get(cls.parent)
                return (parent.key if parent else cls.key, cls.key)
        return ("other", coco_label)

detection_class_registry = DetectionClassRegistry()

# Built-in COCO hierarchy registrations:
BUILTIN_CLASSES = [
    DetectionClass("living_thing", "Living Thing"),
    DetectionClass("animal",       "Animal",    parent="living_thing", coco_ids=[16,17,18,19,20,21,22,23,24,25]),
    DetectionClass("dog",          "Dog",       parent="animal",       coco_ids=[18]),
    DetectionClass("cat",          "Cat",       parent="animal",       coco_ids=[17]),
    DetectionClass("person",       "Person",    parent="living_thing", coco_ids=[1]),
    DetectionClass("vehicle",      "Vehicle",   parent=None,           coco_ids=[2,3,4,5,6,7,8]),
    DetectionClass("car",          "Car",       parent="vehicle",      coco_ids=[3]),
    DetectionClass("furniture",    "Furniture", parent=None,           coco_ids=[57,58,59,60,61,62]),
]
```

#### Extension Point Hook
```python
@hookspec
def register_detection_classes() -> List[DetectionClass]:
    """
    Register additional detection classes / subclasses.
    Example: a medical module adds {"organ", "tumor"} mapped to custom model labels.
    """
```

#### Processor Implementation

```python
class ObjectDetectionProcessor:
    # Read from settings so DAM_DETECTION_THRESHOLD env var is respected (default 0.50)
    @property
    def CONFIDENCE_THRESHOLD(self) -> float:
        return settings.DAM_DETECTION_THRESHOLD

    def _load_model(self):
        import torchvision
        self._model = torchvision.models.detection.ssdlite320_mobilenet_v3_large(
            weights="DEFAULT"
        ).eval()
        self._labels = torchvision.datasets.CocoDetection.COCO_CLASSES  # 80 labels

    def detect(self, path: Path) -> list[dict]:
        from torchvision.transforms.functional import to_tensor
        img_t = to_tensor(Image.open(path).convert("RGB")).unsqueeze(0)
        with torch.no_grad():
            preds = self._model(img_t)[0]
        results = []
        for box, label, score in zip(preds["boxes"], preds["labels"], preds["scores"]):
            if score < self.CONFIDENCE_THRESHOLD:
                continue
            raw_label = self._labels[label.item()]
            cls, subcls = detection_class_registry.resolve(raw_label)
            results.append({
                "class":      cls,
                "subclass":   subcls,
                "confidence": round(score.item(), 4),
                "bbox":       [round(v, 1) for v in box.tolist()],
                "model":      "mobilenet_v3_ssd",
            })
        return results

    async def process(self, asset: Asset, vector_service: VectorService) -> None:
        if "image" not in asset.asset_types:
            return
        path = _urn_to_path(asset.storage_urn)
        objects = await asyncio.to_thread(self.detect, path)
        asset.detected_objects = objects

        # Merge detected classes into tags for unified text search
        detected_tags = list({o["subclass"] for o in objects})
        asset.tags = list(set(asset.tags + detected_tags))

        # Store MobileNet feature vector in Qdrant for visual similarity
        feat = await asyncio.to_thread(self._extract_feature_vector, path)
        await vector_service.upsert_vector(str(asset.id), "mobilenet", feat)
        asset.vectors_indexed["mobilenet"] = True

        await asset.save()

    def _extract_feature_vector(self, path: Path) -> list[float]:
        """Extract 1280-dim MobileNetV3 penultimate layer features."""
        import torchvision.models as models
        backbone = models.mobilenet_v3_large(weights="DEFAULT")
        backbone.classifier = torch.nn.Identity()  # remove classifier head
        backbone.eval()
        from torchvision.transforms.functional import to_tensor
        img_t = to_tensor(Image.open(path).convert("RGB")).unsqueeze(0)
        with torch.no_grad():
            feat = backbone(img_t).squeeze(0)
        return feat.tolist()  # 1280-dim
```

#### Asset Relations via Vector Similarity

When MobileNet, BLIP, and CLIP vectors are computed, the pipeline creates `Link` edges for visually similar assets automatically:

```python
async def create_vector_relations(asset: Asset, vector_service: VectorService):
    """
    Query Qdrant for nearest neighbors using all available vectors.
    Create 'visually_similar_to' Links to high-scoring matches.
    """
    # Read from settings so DAM_VECTOR_RELATION_THRESHOLD env var is respected (default 0.85)
    THRESHOLD = settings.DAM_VECTOR_RELATION_THRESHOLD
    related_ids: Dict[str, float] = {}  # asset_id → max score across vectors

    for vec_name in ["clip", "mobilenet", "blip_text"]:
        if not asset.vectors_indexed.get(vec_name):
            continue
        # Fetch this asset's own vector to use as query
        point = await vector_service.client.retrieve(
            DAM_COLLECTION, ids=[str(asset.id)], with_vectors=[vec_name]
        )
        if not point or vec_name not in point[0].vectors:
            continue
        query_vec = point[0].vectors[vec_name]
        neighbors = await vector_service.search(vec_name, query_vec, limit=10)
        for hit in neighbors:
            if hit["asset_id"] == str(asset.id):
                continue
            if hit["score"] >= THRESHOLD:
                prev = related_ids.get(hit["asset_id"], 0.0)
                # Weight: average across vector types; clip has higher priority
                weight = {"clip": 1.0, "mobilenet": 0.7, "blip_text": 0.8}.get(vec_name, 0.5)
                related_ids[hit["asset_id"]] = max(prev, hit["score"] * weight)

    for target_id, score in related_ids.items():
        await Link(
            source_id=asset.id,
            source_type="Asset",
            target_id=PydanticObjectId(target_id),
            target_type="Asset",
            relation="visually_similar_to",
            weight=round(score, 4),
            metadata={"computed_by": "vector_pipeline"},
        ).insert()
```

---

### 5.6. `UnifiedSearchService` — Semantic + Keyword + Graph

**Architecture:** Three independent channels, merged with proper **Reciprocal Rank Fusion (RRF)**, then filtered, sorted, and paginated using cursor-based pagination.

```
     User Query (SearchRequest)
            │
     ┌──────┴──────────────────────────┐
     │                                 │
 keyword_channel()               vector_channel()
 MongoDB $text index              Qdrant ANN
 (filename, title,                (clip_text  ← text query
  tags, ai_tags,                   clip       ← image query
  ai_caption, desc)                blip_text  ← combined)
     │                                 │
     └──────────────┬──────────────────┘
                    │  RRF(k=60): score = Σ 1/(k + rank_in_channel)
                    ▼
             Candidate Pool (≤ 200 ids)
                    │
             apply_filters()    ← post-filter on MongoDB fields
                    │          (asset_types, tags, status, date, size, owner)
             graph_expand()     ← optional: add related assets via Links
                    │
             fetch_assets()     ← single $in query, preserves ID order
                    │
             SearchPage(items, next_cursor, total_estimate, facets?)
```

> [!NOTE]
> Filters are applied **after** ranking, not inside Qdrant. This keeps the ANN recall high and lets MongoDB enforce ownership/visibility without leaking private assets through vector scores.

---

#### 5.6.1. Request & Response Models

```python
# src/modules/dam/schemas/search.py
from __future__ import annotations
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# ─── Filter Grammar ───────────────────────────────────────────────────────────

class DateRangeFilter(BaseModel):
    after:  Optional[datetime] = None   # ISO-8601
    before: Optional[datetime] = None

class SizeRangeFilter(BaseModel):
    min_bytes: Optional[int] = None
    max_bytes: Optional[int] = None

class AssetFilter(BaseModel):
    """
    All fields are AND-combined.
    List fields use OR semantics within the field (e.g. types=["image","video"]
    → asset_types overlaps with ["image","video"]).
    """
    types:           Optional[List[str]] = None  # filter by asset_types[$in]
    tags:            Optional[List[str]] = None  # manual tags (AND)
    ai_tags:         Optional[List[str]] = None  # AI tags (AND)
    detected_class:  Optional[str]       = None  # detected_objects.class exact match
    status:          Optional[List[Literal[
                         "uploading","processing","ready","missing","error"
                     ]]]                 = None
    has_caption:     Optional[bool]      = None  # asset.ai_caption is not None
    has_vectors:     Optional[bool]      = None  # any key in asset.vectors_indexed
    visibility:      Optional[Literal["private","public","shared"]] = None
    created:         Optional[DateRangeFilter]  = None
    size:            Optional[SizeRangeFilter]  = None
    owner_id:        Optional[str]       = None  # admin-only

    def to_mongo_match(self) -> dict:
        """Build a MongoDB aggregation $match stage from this filter."""
        m: dict = {}
        if self.types:
            m["asset_types"] = {"$in": self.types}
        if self.tags:
            m["tags"] = {"$all": self.tags}
        if self.ai_tags:
            m["ai_tags"] = {"$all": self.ai_tags}
        if self.detected_class:
            m["detected_objects.class"] = self.detected_class
        if self.status:
            m["status"] = {"$in": self.status}
        if self.has_caption is True:
            m["ai_caption"] = {"$ne": None}
        elif self.has_caption is False:
            m["ai_caption"] = None
        if self.has_vectors is True:
            m["vectors_indexed"] = {"$ne": {}}
        if self.visibility:
            m["visibility"] = self.visibility
        if self.created:
            m.setdefault("created_at", {})
            if self.created.after:
                m["created_at"]["$gte"] = self.created.after
            if self.created.before:
                m["created_at"]["$lte"] = self.created.before
        if self.size:
            m.setdefault("size", {})
            if self.size.min_bytes:
                m["size"]["$gte"] = self.size.min_bytes
            if self.size.max_bytes:
                m["size"]["$lte"] = self.size.max_bytes
        return m

# ─── Search Request ───────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    """
    Unified search request accepted by POST /api/dam/search.
    All fields are optional — omitting `q` and `image_asset_id` returns
    a filtered gallery page, sorted by sort_by.
    """
    q:              Optional[str]       = Field(None, description="Free-text query")
    image_asset_id: Optional[str]       = Field(None, description="ID of an ingested asset to use as visual query (reverse image search)")

    filter:         AssetFilter         = Field(default_factory=AssetFilter)

    sort_by:        Literal[
                        "relevance",    # default when q or image_asset_id is set
                        "created_desc", # newest first
                        "created_asc",  # oldest first
                        "size_desc",    # largest first
                        "filename_asc", # alphabetical
                    ]                   = "relevance"

    include_facets: bool                = Field(False, description="Include aggregated facet counts in response")
    graph_expand:   bool                = Field(False, description="Expand result set to include related assets via Links")
    graph_depth:    int                 = Field(1, ge=1, le=3)

    limit:          int                 = Field(30, ge=1, le=200)
    cursor:         Optional[str]       = Field(None, description="Opaque cursor from previous response for pagination")

    @field_validator("q")
    @classmethod
    def strip_q(cls, v):
        return v.strip() if v else None

# ─── Search Response ──────────────────────────────────────────────────────────

class AssetSearchHit(BaseModel):
    """A single search result with its score and matched channels."""
    asset:          Asset
    score:          float               # RRF fused score (0.0 – 1.0 normalized)
    matched_by:     List[Literal["keyword","vector","graph"]]  # which channels contributed

class FacetBucket(BaseModel):
    value:  str
    count:  int

class SearchFacets(BaseModel):
    """Present only when include_facets=true."""
    types:          List[FacetBucket]
    ai_tags:        List[FacetBucket]   # top 20 AI tags in result set
    detected_class: List[FacetBucket]
    status:         List[FacetBucket]

class SearchPage(BaseModel):
    """
    Cursor-based page. Decode cursor with base64(json({last_score, last_id})).
    next_cursor is None when there are no more results.
    """
    items:          List[AssetSearchHit]
    next_cursor:    Optional[str]       = None
    total_estimate: int                 # approximate total matching assets (MongoDB count)
    facets:         Optional[SearchFacets] = None
    query_meta: dict = Field(default_factory=dict)
    # e.g. {"channels_used": ["keyword","vector"], "rrf_k": 60, "latency_ms": 42}
```

---

#### 5.6.2. `UnifiedSearchService` — Full Implementation

```python
# src/modules/dam/services/unified_search.py
import asyncio, base64, json, time
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from ..schemas.search import (
    SearchRequest, SearchPage, AssetSearchHit, SearchFacets, FacetBucket, AssetFilter
)
from ..models import Asset, AssetStatus
from .vector_service import VectorService


RRF_K = 60   # Standard RRF constant. Higher = smoother blend, less rank-sensitive.


def _rrf_score(ranks: List[int]) -> float:
    """Correct RRF: sum of 1/(k + rank) across all channels (1-indexed rank)."""
    return sum(1.0 / (RRF_K + r) for r in ranks)


class UnifiedSearchService:

    def __init__(self, vector_service: VectorService):
        self._vector = vector_service
        self._clip: Optional["CLIPEmbeddingProcessor"] = None  # lazy-loaded

    def _get_clip(self) -> "CLIPEmbeddingProcessor":
        if self._clip is None:
            from ..processors.clip_processor import CLIPEmbeddingProcessor
            self._clip = CLIPEmbeddingProcessor()
        return self._clip

    # ── Public API ─────────────────────────────────────────────────────────────

    async def search(self, req: SearchRequest, owner_id: str) -> SearchPage:
        t0 = time.monotonic()
        channels_used: List[str] = []

        # ── Step 1: Gather ranked lists from each channel ─────────────────────
        kw_ranked:  List[str] = []   # ordered asset_id lists
        vec_ranked: List[str] = []

        tasks = []
        if req.q:
            tasks.append(self._keyword_channel(req.q, owner_id, req.filter, limit=200))
        if req.q or req.image_asset_id:
            tasks.append(self._vector_channel(req.q, req.image_asset_id, owner_id, req.filter, limit=200))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        raw_kw:  List[Tuple[str, str]] = []  # (asset_id, channel)
        raw_vec: List[Tuple[str, str]] = []

        idx = 0
        if req.q:
            if not isinstance(results[idx], Exception):
                kw_ranked = results[idx]
                channels_used.append("keyword")
            idx += 1
        if req.q or req.image_asset_id:
            if not isinstance(results[idx], Exception):
                vec_ranked = results[idx]
                channels_used.append("vector")

        # ── Step 2: RRF Fusion ────────────────────────────────────────────────
        #  Build channel_ranks: {asset_id: [rank_kw, rank_vec, ...]}
        channel_ranks: Dict[str, List[int]] = {}
        for rank, aid in enumerate(kw_ranked, start=1):
            channel_ranks.setdefault(aid, [])
            channel_ranks[aid].append(rank)
        for rank, aid in enumerate(vec_ranked, start=1):
            channel_ranks.setdefault(aid, [])
            # pad with a penalty rank if not in keyword results
            channel_ranks[aid].append(rank)

        if not channel_ranks and (req.q or req.image_asset_id):
            # No results from any channel → return empty
            return SearchPage(items=[], total_estimate=0,
                              query_meta={"channels_used": channels_used})

        # ── Step 3: Score, decode cursor, slice ───────────────────────────────
        scored = {
            aid: _rrf_score(ranks)
            for aid, ranks in channel_ranks.items()
        }

        # If no semantic query → pure filter/sort gallery mode
        if not req.q and not req.image_asset_id:
            return await self._gallery_page(req, owner_id, t0)

        # Determine sort
        sorted_ids = sorted(scored, key=scored.__getitem__, reverse=True)

        # Cursor: opaque base64-encoded {last_score, last_id}
        cursor_offset = self._decode_cursor(req.cursor)
        paged_ids = sorted_ids[cursor_offset: cursor_offset + req.limit]

        # ── Step 4: Graph expand (optional) ──────────────────────────────────
        graph_ids: Dict[str, str] = {}  # extra_asset_id → source_asset_id
        if req.graph_expand and paged_ids:
            graph_ids = await self._graph_expand(paged_ids, depth=req.graph_depth)
            extra = [aid for aid in graph_ids if aid not in scored]
            paged_ids = paged_ids + extra

        # ── Step 5: Fetch & filter assets ────────────────────────────────────
        mongo_filter = req.filter.to_mongo_match()
        mongo_filter["owner_id"] = owner_id  # always enforce ownership
        mongo_filter["_id"] = {"$in": [_to_oid(i) for i in paged_ids]}

        assets_raw = await Asset.find(mongo_filter).to_list(None)
        asset_map = {str(a.id): a for a in assets_raw}

        hits: List[AssetSearchHit] = []
        for aid in paged_ids:
            a = asset_map.get(aid)
            if not a:
                continue
            channels: List[str] = []
            if aid in kw_ranked: channels.append("keyword")
            if aid in vec_ranked: channels.append("vector")
            if aid in graph_ids:  channels.append("graph")
            hits.append(AssetSearchHit(
                asset=a,
                score=round(scored.get(aid, 0.0), 6),
                matched_by=channels,
            ))

        # ── Step 6: Build next cursor ─────────────────────────────────────────
        next_cursor = None
        next_offset = cursor_offset + req.limit
        if next_offset < len(sorted_ids):
            next_cursor = self._encode_cursor(next_offset)

        # ── Step 7: Facets (optional) ─────────────────────────────────────────
        facets = None
        if req.include_facets:
            facets = await self._compute_facets(mongo_filter, asset_map)

        latency_ms = round((time.monotonic() - t0) * 1000)
        return SearchPage(
            items=hits,
            next_cursor=next_cursor,
            total_estimate=len(scored),
            facets=facets,
            query_meta={
                "channels_used": channels_used,
                "rrf_k": RRF_K,
                "latency_ms": latency_ms,
            },
        )

    async def find_similar(self, asset: Asset, limit: int = 20) -> SearchPage:
        """
        Multi-channel visual similarity using all available indexed vectors.
        Falls back to pHash similarity if no Qdrant vectors exist yet.
        """
        candidates: Dict[str, List[int]] = {}
        vec_weights = [("clip", 1.0), ("mobilenet", 0.7), ("blip_text", 0.8)]

        for vec_name, _ in vec_weights:
            if not asset.vectors_indexed.get(vec_name):
                continue
            # Retrieve this asset's stored vector and use it as query
            points = await self._vector.client.retrieve(
                "dam_assets", ids=[str(asset.id)], with_vectors=[vec_name]
            )
            if not points or vec_name not in (points[0].vectors or {}):
                continue
            query_vec = points[0].vectors[vec_name]
            hits = await self._vector.search(vec_name, query_vec, limit=limit * 3)
            for rank, h in enumerate(hits, start=1):
                if h["asset_id"] == str(asset.id):
                    continue
                candidates.setdefault(h["asset_id"], []).append(rank)

        # Fallback: pHash similarity via MongoDB (when no vectors exist)
        if not candidates and asset.phash:
            similar = await Asset.find(
                {"phash": asset.phash, "_id": {"$ne": asset.id},
                 "status": AssetStatus.READY}
            ).limit(limit).to_list(None)
            hits = [
                AssetSearchHit(asset=a, score=1.0, matched_by=["keyword"])
                for a in similar
            ]
            return SearchPage(items=hits, total_estimate=len(hits))

        scored = {aid: _rrf_score(ranks) for aid, ranks in candidates.items()}
        sorted_ids = sorted(scored, key=scored.__getitem__, reverse=True)[:limit]

        assets_raw = await Asset.find(
            {"_id": {"$in": [_to_oid(i) for i in sorted_ids]},
             "status": AssetStatus.READY}
        ).to_list(None)
        asset_map = {str(a.id): a for a in assets_raw}

        hits = [
            AssetSearchHit(asset=asset_map[aid], score=round(scored[aid], 6),
                           matched_by=["vector"])
            for aid in sorted_ids if aid in asset_map
        ]
        return SearchPage(items=hits, total_estimate=len(hits))

    # ── Internal Channels ──────────────────────────────────────────────────────

    async def _keyword_channel(
        self, query: str, owner_id: str, f: AssetFilter, limit: int
    ) -> List[str]:
        """MongoDB full-text search across text-indexed fields."""
        match = f.to_mongo_match()
        match["owner_id"] = owner_id
        match["$text"] = {"$search": query}
        match["status"] = AssetStatus.READY
        pipeline = [
            {"$match": match},
            {"$addFields": {"_score": {"$meta": "textScore"}}},
            {"$sort": {"_score": -1}},
            {"$limit": limit},
            {"$project": {"_id": 1}},
        ]
        docs = await Asset.aggregate(pipeline).to_list(None)
        return [str(d["_id"]) for d in docs]

    async def _vector_channel(
        self, query: Optional[str], image_asset_id: Optional[str],
        owner_id: str, f: AssetFilter, limit: int
    ) -> List[str]:
        """
        Qdrant ANN search. Uses clip_text for text queries, clip for image queries.
        When both are provided, fetches from both and interleaves by rank.
        """
        clip = self._get_clip()
        results: List[str] = []

        if query:
            text_vec = await asyncio.to_thread(clip.embed_text, query)
            hits = await self._vector.search("clip_text", text_vec, limit=limit)
            results += [h["asset_id"] for h in hits]

        if image_asset_id:
            points = await self._vector.client.retrieve(
                "dam_assets", ids=[image_asset_id], with_vectors=["clip"]
            )
            if points and "clip" in (points[0].vectors or {}):
                img_vec = points[0].vectors["clip"]
                hits = await self._vector.search("clip", img_vec, limit=limit)
                # Interleave image results
                seen = set(results)
                for h in hits:
                    if h["asset_id"] not in seen:
                        results.append(h["asset_id"])
                        seen.add(h["asset_id"])

        return results[:limit]

    async def _gallery_page(
        self, req: SearchRequest, owner_id: str, t0: float
    ) -> SearchPage:
        """Pure filter+sort path — no semantic channels needed."""
        mongo_filter = req.filter.to_mongo_match()
        mongo_filter["owner_id"] = owner_id
        mongo_filter.setdefault("status", AssetStatus.READY)

        sort_map = {
            "created_desc": [("created_at", -1)],
            "created_asc":  [("created_at",  1)],
            "size_desc":    [("size",        -1)],
            "filename_asc": [("filename",     1)],
            "relevance":    [("created_at",  -1)],   # fallback
        }
        sort = sort_map.get(req.sort_by, [("created_at", -1)])

        cursor_offset = self._decode_cursor(req.cursor)
        total = await Asset.find(mongo_filter).count()
        assets = await (
            Asset.find(mongo_filter)
                 .sort(sort)
                 .skip(cursor_offset)
                 .limit(req.limit)
                 .to_list(None)
        )

        hits = [AssetSearchHit(asset=a, score=0.0, matched_by=[]) for a in assets]
        next_cursor = (
            self._encode_cursor(cursor_offset + req.limit)
            if cursor_offset + req.limit < total else None
        )
        facets = None
        if req.include_facets:
            facets = await self._compute_facets(mongo_filter, {str(a.id): a for a in assets})

        return SearchPage(
            items=hits,
            next_cursor=next_cursor,
            total_estimate=total,
            facets=facets,
            query_meta={"mode": "gallery", "latency_ms": round((time.monotonic() - t0)*1000)},
        )

    async def _graph_expand(self, asset_ids: List[str], depth: int) -> Dict[str, str]:
        """
        Walk `visually_similar_to` and `contains` links up to `depth` hops.
        Returns {extra_id: source_id}.
        """
        from ..models import Link
        extra: Dict[str, str] = {}
        frontier = set(asset_ids)
        for _ in range(depth):
            links = await Link.find(
                {"source_id": {"$in": [_to_oid(i) for i in frontier]},
                 "relation": {"$in": ["visually_similar_to", "contains"]}}
            ).to_list(None)
            new_frontier = set()
            for lnk in links:
                tid = str(lnk.target_id)
                if tid not in frontier and tid not in extra:
                    extra[tid] = str(lnk.source_id)
                    new_frontier.add(tid)
            frontier = new_frontier
            if not frontier:
                break
        return extra

    async def _compute_facets(self, match: dict, _hint_map: dict) -> SearchFacets:
        """MongoDB aggregation to get top-N facet counts for the current result set."""
        def _agg(field: str, n: int = 20):
            return Asset.aggregate([
                {"$match": match},
                {"$unwind": f"${field}"},
                {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": n},
            ])

        types_r, ai_tags_r, class_r, status_r = await asyncio.gather(
            _agg("asset_types").to_list(None),
            _agg("ai_tags").to_list(None),
            _agg("detected_objects.class").to_list(None),
            _agg("status", n=10).to_list(None),
        )
        return SearchFacets(
            types=          [FacetBucket(value=r["_id"], count=r["count"]) for r in types_r],
            ai_tags=        [FacetBucket(value=r["_id"], count=r["count"]) for r in ai_tags_r],
            detected_class= [FacetBucket(value=r["_id"], count=r["count"]) for r in class_r],
            status=         [FacetBucket(value=r["_id"], count=r["count"]) for r in status_r],
        )

    # ── Cursor helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _encode_cursor(offset: int) -> str:
        return base64.urlsafe_b64encode(json.dumps({"o": offset}).encode()).decode()

    @staticmethod
    def _decode_cursor(cursor: Optional[str]) -> int:
        if not cursor:
            return 0
        try:
            return json.loads(base64.urlsafe_b64decode(cursor)).get("o", 0)
        except Exception:
            return 0


def _to_oid(id_str: str):
    from beanie import PydanticObjectId
    return PydanticObjectId(id_str)
```

> **MongoDB Text Index Required** (add to `Asset.Settings.indexes`):
> ```python
> [("filename", "text"), ("title", "text"), ("description", "text"),
>  ("tags", "text"), ("ai_tags", "text"), ("ai_caption", "text")],
> ```

---

## 7. API Reference

All endpoints are under the prefix **`/api/dam`** and require `Authorization: Bearer <token>`.  
All list/search responses use `SearchPage`; single-asset responses use `Asset`.

---

### 7.1. Asset CRUD

| Method | Path | Body / Params | Response | Notes |
|--------|------|---------------|----------|-------|
| `POST` | `/upload` | `multipart/form-data` | `Asset` | Queues `pipeline_task`. |
| `POST` | `/register` | `{"path": "..."}` | `Asset` | Registers an already-on-disk file — NAS import. |
| `POST` | `/ingest/url` | `{"url":"...","title":"..."}` | `Asset` | Creates a virtual URL asset. |
| `GET` | `/assets/{id}` | — | `Asset` | Full asset including AI fields. |
| `PATCH` | `/assets/{id}` | Partial `Asset` fields | `Asset` | Only `title`, `description`, `tags`, `visibility`. |
| `DELETE` | `/assets/{id}` | `?hard=false` | `204` | Soft-delete by default (marks MISSING). |
| `GET` | `/assets/{id}/download` | — | `StreamingResponse` | Streams original file via AFS; sets `Content-Disposition`. |
| `GET` | `/assets/{id}/thumbnail/{size}` | `size=small\|medium\|large` | redirect to WebP | 302 → signed AFS URL. |

---

### 7.2. Search & Discovery

#### `POST /api/dam/search` — Unified Search (primary endpoint)

Accepts a `SearchRequest` body. All fields are optional.

**Request** (`application/json`):
```json
{
  "q": "golden retriever puppy",
  "filter": {
    "types": ["image"],
    "ai_tags": ["dog"],
    "status": ["ready"],
    "created": { "after": "2024-01-01T00:00:00Z" }
  },
  "sort_by": "relevance",
  "include_facets": true,
  "graph_expand": false,
  "limit": 30,
  "cursor": null
}
```

**Response** (`SearchPage`):
```json
{
  "items": [
    {
      "asset": { "id": "...", "filename": "puppy.jpg", "ai_caption": "a golden retriever puppy playing in grass", "..." : "..." },
      "score": 0.031847,
      "matched_by": ["vector", "keyword"]
    }
  ],
  "next_cursor": "eyJvIjogMzB9",
  "total_estimate": 142,
  "facets": {
    "types":          [{"value": "image", "count": 138}, {"value": "video", "count": 4}],
    "ai_tags":        [{"value": "dog", "count": 55}, {"value": "outdoor", "count": 30}],
    "detected_class": [{"value": "animal", "count": 61}],
    "status":         [{"value": "ready", "count": 142}]
  },
  "query_meta": { "channels_used": ["keyword", "vector"], "rrf_k": 60, "latency_ms": 87 }
}
```

**Pagination:** Pass `cursor` from `next_cursor` of the previous response. Do not parse the cursor — treat it as opaque.

---

#### `GET /api/dam/search` — Quick Search (GET convenience alias)

For simple UI typeahead or URL-shareable searches. Maps to `POST /search` internally.

| Param | Type | Example | Description |
|-------|------|---------|-------------|
| `q` | string | `sunset beach` | Free-text query |
| `types` | CSV | `image,video` | Filter by asset_types |
| `tags` | CSV | `nature,travel` | Manual tags (AND) |
| `ai_tags` | CSV | `outdoor,sunset` | AI tags (AND) |
| `class` | string | `animal` | Detected object class |
| `status` | CSV | `ready` | Asset status |
| `after` | ISO date | `2024-01-01` | Created after |
| `before` | ISO date | `2025-01-01` | Created before |
| `min_size` | int | `1048576` | Min file size in bytes |
| `max_size` | int | `104857600` | Max file size |
| `has_caption` | bool | `true` | Only AI-captioned assets |
| `has_vectors` | bool | `true` | Only vectorized assets |
| `sort` | enum | `created_desc` | Sort order |
| `limit` | int (1–200) | `30` | Page size |
| `cursor` | string | `eyJvIjogMzB9` | Pagination cursor |
| `facets` | bool | `true` | Include facet counts |

**Examples:**
```
GET /api/dam/search?q=invoice&types=document&status=ready&limit=20
GET /api/dam/search?types=image&ai_tags=outdoor,sunrise&sort=created_desc
GET /api/dam/search?class=person&has_vectors=true&facets=true
GET /api/dam/search?q=red+car&sort=relevance&limit=30&cursor=eyJvIjogMzB9
```

---

#### `POST /api/dam/search/image` — Reverse Image Search

Upload any image file to find visually similar indexed assets using CLIP embeddings.

```
POST /api/dam/search/image
Content-Type: multipart/form-data

file:     <binary image (JPEG/PNG/WEBP, max 10 MB)>
limit:    20                (optional, default 20, max 200)
types:    image,video       (optional CSV filter)
```

**Response:** `SearchPage` — same schema as `POST /search`. All hits have `matched_by: ["vector"]`.

---

#### `GET /api/dam/assets/{id}/similar` — Asset-to-Asset Similarity

```
GET /api/dam/assets/{id}/similar?limit=20&types=image
```

Uses all available indexed Qdrant vectors (`clip`, `mobilenet`, `blip_text`) fused via RRF. Falls back to perceptual hash (`phash`) matching if vectors are not yet indexed.

**Response:** `SearchPage` with `matched_by: ["vector"]` per hit.

---

#### `GET /api/dam/assets/{id}/objects` — Detected Objects

```json
// Response
{
  "asset_id": "...",
  "detected_objects": [
    {"class": "animal", "subclass": "dog",  "confidence": 0.97, "bbox": [120, 45, 380, 290], "model": "mobilenet_v3_ssd"},
    {"class": "person", "subclass": "person","confidence": 0.88, "bbox": [10, 5, 200, 480], "model": "mobilenet_v3_ssd"}
  ]
}
```

---

### 7.3. Facets (Stand-alone)

```
GET /api/dam/facets?types=image&status=ready
```

Returns `SearchFacets` for the given filters without returning any assets. Useful for populating sidebar filter counts independently of a search query.

```json
{
  "types":           [{"value": "image", "count": 1204}],
  "ai_tags":         [{"value": "outdoor", "count": 300}, {"value": "portrait", "count": 211}],
  "detected_class":  [{"value": "person", "count": 452}, {"value": "animal", "count": 130}],
  "status":          [{"value": "ready", "count": 1204}]
}
```

---

### 7.4. Graph Traversal

```
GET /api/dam/assets/{id}/links?relation=visually_similar_to&depth=1
```

| Param | Default | Description |
|-------|---------|-------------|
| `relation` | (all) | Filter by relation type |
| `direction` | `outgoing` | `outgoing` \| `incoming` \| `both` |
| `depth` | `1` | Hops (1–3) |
| `limit` | `20` | Max related assets to return |

```json
{
  "source_id": "...",
  "edges": [
    {"target_id": "...", "relation": "visually_similar_to", "weight": 0.92, "asset": {...}},
    {"target_id": "...", "relation": "contains",            "weight": 1.0,  "asset": {...}}
  ]
}
```

---

### 7.5. AI Pipeline Management

```
POST /api/dam/assets/{id}/reprocess          # Re-queue full AI pipeline
POST /api/dam/assets/{id}/reprocess?steps=blip,clip   # Specific processors only
GET  /api/dam/pipeline/status                # Coverage stats for all assets
```

**`GET /api/dam/pipeline/status` response:**
```json
{
  "total_assets": 2048,
  "ready":        1804,
  "processing":     44,
  "error":          12,
  "vectors": {
    "clip":      {"indexed": 1750, "coverage_pct": 85.4},
    "blip_text": {"indexed": 1690, "coverage_pct": 82.5},
    "mobilenet": {"indexed": 1601, "coverage_pct": 78.2},
    "clip_text": {"indexed": 1690, "coverage_pct": 82.5}
  },
  "ai_captions_generated": 1690,
  "ai_tags_generated": 1750
}
```

---

### 7.6. Albums

| Method | Path | Notes |
|--------|------|-------|
| `GET` | `/albums` | List user's albums |
| `POST` | `/albums` | Create album (`name`, `description`) |
| `GET` | `/albums/{id}` | Album detail + asset count |
| `POST` | `/albums/{id}/assets` | Add assets (`asset_ids: []`) |
| `DELETE` | `/albums/{id}/assets/{asset_id}` | Remove asset from album |
| `DELETE` | `/albums/{id}` | Delete album (does not delete assets) |
| `GET` | `/albums/{id}/search` | Search *within* album — same params as `GET /search` |




### 6.1. `AssetGallery`
- A responsive grid view of asset thumbnails.
- **Features**:
    - Infinite scroll or pagination.
    - Drag & Drop upload zone.
    - Sidebar filters (Type, Date, Tags, **AI tags**, detected objects).
    - Multi-select for bulk actions (Delete, Tag).
    - "Find Similar" button (triggers UnifiedSearchService.find_similar).

### 6.2. `AssetViewer` (Lightbox)
- Modal dialog for viewing the full-size asset.
- **Inspector Sidebar** (Layered Tabs):
    -   **General**: Core + Technical info + `ai_caption`.
    -   **AI Tags**: `ai_tags` confidence chart + `detected_objects` overlay with bbox.
    -   **Modules**: Dynamic tabs for each Namespace (Visualized via DataExplorer).
    -   **Graph**: Visualizes immediate neighbors including `visually_similar_to` links.
- "Copy Link" / "Download" / "Find Similar" actions.

### 6.3. `GraphExplorer`
- **Visualization**: Interactive node-link diagram using **Cytoscape.js** or **D3.js**.
- **Navigation**: Click node to expand neighbors.
- **Breadcrumbs 2.0**: Path-based navigation (e.g., `Project X > contains > Folder Y > includes > Asset Z`).
- Shows `visually_similar_to` edges from vector pipeline.

### 6.4. `AssetPicker` (Widget)
- A reusable component that other modules (e.g., Blog, Page Builder) can open to select an asset.
- Returns the `Asset` object or public URL.
- Supports semantic search via UnifiedSearchService.

## 7. API Endpoints

### 7.1. Assets CRUD
- `POST /api/dam/upload`: Multipart upload.
- `GET /api/dam/assets`: List with filters (`type`, `tags`, `class`, `status`).
- `GET /api/dam/assets/{id}`: Detail view.
- `PATCH /api/dam/assets/{id}`: Update metadata.
- `DELETE /api/dam/assets/{id}`: Delete (Soft or Hard).

### 7.2. Search & Discovery
- `GET /api/dam/search?q=<text>&type=image&class=dog&limit=30`
- `POST /api/dam/search/image` — query by image upload (CLIP reverse image search)
- `GET /api/dam/assets/{id}/similar` — multi-vector similarity
- `GET /api/dam/assets/{id}/objects` — object detection results with bbox

### 7.3. AI Pipeline Management
- `POST /api/dam/assets/{id}/reprocess` — re-run full AI pipeline on an asset
- `GET /api/dam/vectors/status` — index coverage stats (how many assets have each vector)

## 8. Roadmap

- [ ] **Phase 0**: Core Framework Prerequisites (see §9) — async startup hook, `register_services`, `register_pipeline_processors`, named `ServiceRegistry`, DAM/Qdrant env vars in `config.py`.
- [ ] **Phase 1**: Basic Upload, Storage (AFS), and Gallery View.
- [ ] **Phase 2**: Thumbnail Generation & Metadata Extraction (pyexiv2, ffprobe).
- [ ] **Phase 3**: BLIP Captioning + CLIP Embeddings + Qdrant Setup.
- [ ] **Phase 4**: Smile/Wolf Auto-Tagger + MobileNet Object Detection.
- [ ] **Phase 5**: UnifiedSearchService (semantic + keyword + graph RRF).
- [ ] **Phase 6**: Image Editor (Crop/Region extraction) & Asset Picker Widget.
- [ ] **Phase 7**: Large File Support (TUS Protocol, Chunked Uploads).

---

## 9. Framework Integration — Phase 0 Core Changes

> [!IMPORTANT]
> These are **required changes to `src/core/`** that must land before any DAM implementation begins. They address real gaps found by reading the actual codebase.

| Core File | Change | DAM Component That Needs It |
|---|---|---|
| `hooks.py` | +6 hookspecs (see below) | All DAM services |
| `registry.py` | `register_named` / `get_named` | Cross-module VectorService access |
| `config.py` | DAM + Qdrant env vars | VectorService, WatcherService, AI pipeline |
| `module_loader.py` | `register_module_services()` lifecycle step | Service wiring before startup |
| `main.py` | Await `on_startup_async` in lifespan | WatcherService, Qdrant bootstrap |

**Six new hookspecs** (up from 5 in the original plan — `register_asset_types` was discovered in §3.1):

| Hookspec | Purpose |
|---|---|
| `register_services` | Wire services into `ServiceRegistry` after DB init |
| `on_startup_async` | Async startup (Qdrant bootstrap, WatcherService.start) |
| `register_pipeline_processors` | Inject pipeline processors (BLIP, CLIP, MobileNet…) |
| `register_asset_drivers` | Inject typed drivers into `AssetDriverRegistry` |
| `register_asset_types` | Register `AssetTypeDefinition` entries into `AssetTypeRegistry` |
| `register_vector_definitions` | Register additional Qdrant named vectors |

---

### 9.1. `hooks.py` — Six New Hookspecs

```python
# src/core/hooks.py  (additions to WebOSHookSpec)

@hookspec
def register_services():
    """
    Instantiate and register module services with ServiceRegistry.
    Called AFTER init_db(), BEFORE on_startup(). This is where DAM wires
    VectorService, WatcherService, AssetDriverManager into the registry.
    """

@hookspec
async def on_startup_async():
    """
    Async startup — awaited by the lifespan manager.
    Use instead of on_startup() for any I/O-bound startup work.
    DAM: await VectorService.ensure_collection(), await WatcherService.start().
    """

@hookspec
def register_pipeline_processors() -> List["PipelineProcessor"]:
    """
    Register processors for the TaskIQ pipeline_task worker.
    Built-in DAM processors: [BLIP, CLIP, AutoTagger, MobileNet].
    External modules inject additional processors (e.g. OCR, FaceRecognition).
    """

@hookspec
def register_asset_drivers() -> List["AssetDriver"]:
    """
    Register typed asset drivers with DAM's AssetDriverRegistry.
    External modules add domain-specific drivers (e.g. CADModelDriver).
    """

@hookspec
def register_asset_types() -> List["AssetTypeDefinition"]:
    """
    Register custom asset types with DAM's AssetTypeRegistry.
    Built-in types (image, video, audio, document, url …) are pre-loaded by DAM.
    External modules extend with domain types: e.g. [AssetTypeDefinition("3d_model", ...)]
    """

@hookspec
def register_vector_definitions() -> Dict[str, Tuple[int, Any]]:
    """
    Register additional Qdrant named vectors beyond the DAM defaults.
    Returns {vector_name: (dimension, Distance)}.
    E.g. {"dino_v2": (1536, Distance.COSINE)} from a research module.
    """
```

---

### 9.2. `registry.py` — Named Service Lookup

```python
# src/core/registry.py  (additions to ServiceRegistry)

class ServiceRegistry:
    _named: Dict[str, Any] = {}     # ← NEW alongside existing _services

    @classmethod
    def register_named(cls, name: str, implementation: Any) -> None:
        """
        Register by string name — enables cross-module access without imports.
        DAM:  register_named("dam.vector_service", vs)
        Blog: get_named("dam.vector_service") to embed blog cover images.
        """
        cls._named[name] = implementation

    @classmethod
    def get_named(cls, name: str) -> Any:
        svc = cls._named.get(name)
        if not svc:
            raise ValueError(f"Named service '{name}' not registered.")
        return svc

    @classmethod
    def get_named_optional(cls, name: str) -> Optional[Any]:
        return cls._named.get(name)

    # Also update clear() to include: cls._named.clear()
```

---

### 9.3. `config.py` — DAM & Qdrant Environment Variables

```python
# src/core/config.py  (additions to Settings class)

# ── Qdrant ────────────────────────────────────────────────────────────────────
QDRANT_URL:     str           = "http://localhost:6333"
QDRANT_API_KEY: Optional[str] = None

# ── DAM Module ────────────────────────────────────────────────────────────────
DAM_WATCH_PATHS:              List[str] = []   # e.g. ["/mnt/nas/photos"]
DAM_CACHE_DIR:                str       = "data/dam_cache"
DAM_SYSTEM_OWNER_ID:          Optional[str] = None
DAM_AI_ENABLED:               bool      = False  # Default OFF — opt in per deployment
DAM_TAGGER_THRESHOLD:         float     = 0.35
DAM_DETECTION_THRESHOLD:      float     = 0.50
DAM_VECTOR_RELATION_THRESHOLD:float     = 0.85
```

> [!NOTE]
> `DAM_AI_ENABLED = False` is a safe default. A fresh deployment won't pull 2+ GB of model weights. AI is explicitly opted-in per host via `.env`.

---

### 9.4. `module_loader.py` — `register_services` Lifecycle Step

```python
# src/core/module_loader.py  (addition to ModuleLoader)

def register_module_services(self):
    """
    Call register_services() on all registered plugins.
    MUST be called after init_db(), before trigger_startup().
    """
    self.pm.hook.register_services()
    logger.info("Module services registered.")

async def trigger_startup_async(self):
    """Await all on_startup_async hook results."""
    results = self.pm.hook.on_startup_async()
    for result in results:
        if asyncio.iscoroutine(result):
            await result
```

**Correct startup order:**
```
1. await init_db(all_models)               ← Beanie ready
2. await settings_service.load_all()       ← Persistent settings
3. await setup_default_user()              ← Admin seeded
4. loader.register_module_services()       ← [NEW] services wired
5. loader.trigger_startup()                ← sync hooks
6. await loader.trigger_startup_async()    ← [NEW] async hooks
```

---

### 9.5. `main.py` — Lifespan Update

```python
# src/main.py  (lifespan changes)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    all_models = [User, ModuleSettingsDoc] + loader.get_all_models()
    await init_db(all_models)
    await settings_service.load_all()
    await setup_default_user()

    loader.register_module_services()       # ← NEW (Phase 0)
    loader.trigger_startup()
    await loader.trigger_startup_async()    # ← NEW (Phase 0)

    yield
    loader.trigger_shutdown()
```

---

### 9.6. DAM `hooks.py` — Complete Reference Implementation

```python
# src/modules/dam/hooks.py
import asyncio
from typing import List, Dict, Tuple, Any, Type
from pydantic import BaseModel

from src.core.hooks import hookimpl
from src.core.registry import ServiceRegistry
from src.core.config import settings

from .models import Asset, Link, Album
from .services.asset_service import AssetService
from .services.vector_service import VectorService
from .services.unified_search import UnifiedSearchService
from .drivers.registry import AssetDriverRegistry
from .drivers.manager import AssetDriverManager
from .drivers.image_driver import ImageDriver
from .drivers.video_driver import VideoDriver
from .drivers.url_driver import UrlDriver
from .processors.blip_processor import BLIPCaptioningProcessor
from .processors.clip_processor import CLIPEmbeddingProcessor
from .processors.auto_tagger import AutoTaggerProcessor
from .processors.detection.mobilenet_processor import ObjectDetectionProcessor
from .watcher import WatcherService
from .dam_settings import DAMSettings


class DAMHooks:
    module_name = "dam"

    @hookimpl
    def register_models(self) -> List:
        return [Asset, Link, Album]

    @hookimpl
    def register_settings(self) -> Type[BaseModel]:
        return DAMSettings

    @hookimpl
    def register_services(self):
        """Wire all DAM services into ServiceRegistry."""
        from qdrant_client import AsyncQdrantClient
        from src.core.module_loader import loader

        qdrant = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        vs = VectorService(qdrant)

        # Let other modules extend vector definitions
        for extra in loader.pm.hook.register_vector_definitions():
            vs.extend_definitions(extra or {})

        # Build driver registry, let other modules inject drivers
        driver_reg = AssetDriverRegistry()
        for d in [ImageDriver(), VideoDriver(), UrlDriver()]:
            driver_reg.register(d)
        for drivers in loader.pm.hook.register_asset_drivers():
            for d in (drivers or []):
                driver_reg.register(d)

        asset_svc  = AssetService(vs)
        asset_mgr  = AssetDriverManager(driver_reg)
        search_svc = UnifiedSearchService(vs)

        ServiceRegistry.register(VectorService,        vs)
        ServiceRegistry.register(AssetService,         asset_svc)
        ServiceRegistry.register(AssetDriverManager,   asset_mgr)
        ServiceRegistry.register(UnifiedSearchService, search_svc)

        # String-keyed for cross-module use (no direct DAM import needed)
        ServiceRegistry.register_named("dam.vector_service", vs)
        ServiceRegistry.register_named("dam.search",         search_svc)

    @hookimpl
    async def on_startup_async(self):
        """Bootstrap Qdrant collection and start filesystem watcher."""
        vs = ServiceRegistry.get(VectorService)
        await vs.ensure_collection()

        if settings.DAM_WATCH_PATHS:
            from pathlib import Path
            asset_svc = ServiceRegistry.get(AssetService)
            watcher = WatcherService(asset_svc)
            for p in settings.DAM_WATCH_PATHS:
                watcher.add_watch(Path(p))
            ServiceRegistry.register(WatcherService, watcher)
            await watcher.start()

    @hookimpl
    def register_pipeline_processors(self) -> List:
        if not settings.DAM_AI_ENABLED:
            return []
        return [
            BLIPCaptioningProcessor(),
            CLIPEmbeddingProcessor(),
            AutoTaggerProcessor(),
            ObjectDetectionProcessor(),
        ]

    @hookimpl
    def register_routes(self, app):
        from .router import router
        app.include_router(router)

    @hookimpl
    def register_ui(self):
        from . import ui  # noqa: registers NiceGUI pages

    @hookimpl
    def register_admin_widgets(self):
        from .admin_widget import DAMStatsWidget  # noqa


hooks = DAMHooks()
```

---

### 9.7. `DAMSettings` — Runtime-Configurable Settings

```python
# src/modules/dam/dam_settings.py
from pydantic import BaseModel
from typing import List, Optional

class DAMSettings(BaseModel):
    """
    Runtime settings stored in MongoDB system_settings collection.
    Users adjust these via Admin UI; config.py env vars provide first-boot defaults.
    """
    watch_paths:               List[str] = []
    cache_dir:                 str       = "data/dam_cache"
    ai_enabled:                bool      = False
    tagger_threshold:          float     = 0.35
    detection_threshold:       float     = 0.50
    vector_relation_threshold: float     = 0.85
    auto_create_relations:     bool      = True
    thumbnail_sizes:           List[int] = [128, 512, 1024]

    class Config:
        title = "DAM Module Settings"
```

> [!TIP]
> `DAMSettings` fields mirror the `config.py` env vars. `settings_service` loads runtime overrides from the DB after `config.py` provides the initial defaults — giving both per-deployment env control and per-user runtime tuning.

---

## 10. UI & Settings Integration (Phase 0 Prerequisite)

> [!IMPORTANT]
> This section documents the framework's existing UI surface points, the gaps discovered during DAM planning, the **5 targeted framework enhancements** needed, and the complete map of how DAM plugs into every UI slot. All framework changes here must land alongside Phase 0 (§9) before DAM Phase 1 begins.

---

### 10.1. Framework UI Surface Inventory

The WebOS shell provides the following pluggable surfaces. All are populated at startup via hooks or registries — no runtime configuration needed.

| Surface | Mechanism | Where Rendered |
|---------|-----------|----------------|
| **Launchpad grid** | `UIRegistry.register_app(AppMetadata)` | `/` dashboard |
| **Sidebar nav links** | Same `AppMetadata` | Left drawer |
| **Command palette** (`⌘K`) | `AppMetadata.commands` string list | Dialog, text search |
| **Dashboard widgets** | `ui_slots.add("dashboard_widgets", fn)` | Below launchpad on `/` |
| **Header actions** | `ui_slots.add("header", fn)` | Top-right of header bar |
| **App grid (extra cards)** | `ui_slots.add("app_grid", fn)` | After registry cards |
| **Sidebar (extra items)** | `ui_slots.add("sidebar", fn)` | Below auto-nav links |
| **Admin widget grid** | `AdminRegistry.register_widget(AdminWidget)` | `/admin` page |
| **Settings panel** | `settings_service.register_schema(name, Model)` | `/admin/settings` via `DataExplorer` |

#### Settings System Flow

```
Module.register_settings() → settings_service.register_schema("dam", DAMSettings)
          ↓ (lifespan startup)
settings_service.load_all() → reads ModuleSettingsDoc from MongoDB → populates _cache
          ↓ (runtime)
settings_service.get("dam")        → returns live DAMSettings instance
settings_service.update("dam", {}) → validates → persists → emits "settings:updated" on EventBus
          ↓ (admin UI)
/admin/settings → DataExplorer renders editable form from schema — zero extra code needed
```

---

### 10.2. Framework Gaps & Required Enhancements

Six gaps were identified by reading the actual framework source. The three marked **Phase 0 required** block DAM functionality without workarounds.

| # | Gap | Severity | Phase 0 Required? |
|---|-----|----------|-------------------|
| 1 | `UI_Slot.add()` silently drops unknown slot names (just prints warning) | Medium | ✅ Yes |
| 2 | Only 4 fixed slot names — can't register the `asset_picker_overlay` global slot | High | ✅ Yes |
| 3 | No `register_page_slots` mechanism — can't inject tabs into other module pages | High | ✅ Yes |
| 4 | `AppMetadata` has no `badge_text` field — can't show "1,204 assets" count | Low | No (Phase 3) |
| 5 | `settings_service.get()` returns untyped `Optional[BaseModel]` | Low | No (Phase 1) |

#### Enhancement A — `UI_Slot`: Open registration + module tagging

#### [MODIFY] `src/ui/layout.py`

```python
class UI_Slot:
    _BUILTIN = {"sidebar", "header", "dashboard_widgets", "app_grid",
                "asset_picker_overlay",          # NEW: DAM global picker modal
                "command_palette_actions"}        # NEW: extra ⌘K actions

    def __init__(self):
        self._slots: Dict[str, List[Callable]] = {s: [] for s in self._BUILTIN}

    def add(self, slot_name: str, builder: Callable, *, module: str = "unknown"):
        if slot_name not in self._slots:
            # Open registration: custom slots allowed, but logged for visibility
            logger.warning(f"[UISlot] '{module}' creating new slot '{slot_name}'")
            self._slots[slot_name] = []
        self._slots[slot_name].append(builder)
```

#### Enhancement B — `PageSlotRegistry` (new file)

Enables a module's page to declare injectable slots that other modules can fill.

#### [NEW] `src/ui/page_slot_registry.py`

```python
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any

@dataclass
class PageSlot:
    page_pattern: str   # e.g. "/dam/assets/{id}"
    slot_name:    str   # e.g. "details_panel"
    builders: List[Callable] = field(default_factory=list)

class PageSlotRegistry:
    def __init__(self):
        self._slots: Dict[str, Dict[str, PageSlot]] = {}

    def declare(self, page_pattern: str, slot_name: str):
        """Called by the page owner to announce an injectable slot."""
        self._slots.setdefault(page_pattern, {})[slot_name] = PageSlot(page_pattern, slot_name)

    def inject(self, page_pattern: str, slot_name: str, builder: Callable):
        """Called by other modules to fill a declared slot."""
        slot = self._slots.get(page_pattern, {}).get(slot_name)
        if slot:
            slot.builders.append(builder)
        else:
            logger.warning(f"[PageSlot] Slot '{page_pattern}:{slot_name}' not declared. Register page first.")

    def render(self, page_pattern: str, slot_name: str, **context):
        """Called inside a page to render all injected builders."""
        for fn in self._slots.get(page_pattern, {}).get(slot_name, PageSlot("","")).builders:
            fn(**context)

page_slot_registry = PageSlotRegistry()
```

#### Enhancement C — `register_page_slots` hookspec

#### [MODIFY] `src/core/hooks.py`

```python
@hookspec
def register_page_slots(registry: "PageSlotRegistry"):
    """
    Declare injectable slots on this module's pages.
    Called during loader.register_ui().

    Example:
        registry.declare("/dam/assets/{id}", "details_panel")
        registry.declare("/dam/assets/{id}", "actions_toolbar")
    """
```

#### [MODIFY] `src/core/module_loader.py` — wire the new hook

```python
def register_ui(self):
    from src.ui.page_slot_registry import page_slot_registry
    # First pass: let all modules declare their injectable slots
    self.pm.hook.register_page_slots(registry=page_slot_registry)
    # Second pass: register UI pages and inject into declared slots
    self.pm.hook.register_ui()
```

#### Enhancement D — `AppMetadata.badge_text` (non-blocking, Phase 3)

#### [MODIFY] `src/ui/registry.py`

```python
@dataclass
class AppMetadata:
    name:             str
    icon:             str
    route:            str
    description:      str       = ""
    category:         str       = "Utilities"
    is_system:        bool      = False
    commands:         List[str] = field(default_factory=list)
    badge_text:       Optional[str] = None   # NEW: e.g. "1,204 assets" shown on launchpad card
    keyboard_shortcut:Optional[str] = None   # NEW: e.g. "Alt+D" shown in ⌘K
```

#### Enhancement E — `settings_service.get_typed()` (non-blocking, Phase 1)

#### [MODIFY] `src/core/services/settings_service.py`

```python
from typing import TypeVar
T = TypeVar("T", bound=BaseModel)

def get_typed(self, module_name: str, schema_class: Type[T]) -> T:
    """Type-safe settings accessor with clear error messages."""
    result = self._cache.get(module_name)
    if result is None:
        raise KeyError(f"Settings for '{module_name}' not loaded. Implement register_settings().")
    if not isinstance(result, schema_class):
        raise TypeError(f"Expected {schema_class.__name__}, got {type(result).__name__}")
    return result

# Usage in DAM:
# dam_cfg = settings_service.get_typed("dam", DAMSettings)
```

---

### 10.3. DAM Integration Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WebOS Shell  /                                  │
│                                                                         │
│  ┌──Launchpad──────────────────────────────────────────────────────┐   │
│  │  [Storage]  [Admin]  [Blogger]  [📷 Media Library ★]  ...      │   │
│  │                                  ↑ AppMetadata + badge_text     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──Sidebar──────────────────────────────────────────────────────────┐ │
│  │  Dashboard │ Storage │ 📷 Media Library ★ │ Admin │ ...           │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──Header────────────────────────────────────────────────────────────┐│
│  │  [≡] WebOS                [☁ Quick Upload ★]  [🌙]  [🔍]  Admin  ││
│  │                            ↑ ui_slots("header")                   ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│  ┌──Dashboard Widgets─────────────────────────────────────────────────┐│
│  │  [System Shell]   [📷 Media Library Stats ★]                      ││
│  │                    ↑ ui_slots("dashboard_widgets")                 ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│  ┌──⌘K Command Palette────────────────────────────────────────────────┐│
│  │  > upload asset  ← AppMetadata.commands                            ││
│  │  > search images ← AppMetadata.commands                            ││
│  │  > find similar  ← AppMetadata.commands                            ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│  ┌──Global Overlay (rendered once, shown on JS event)─────────────────┐│
│  │  [Asset Picker Modal ★]                                             ││
│  │   ↑ ui_slots("asset_picker_overlay")                               ││
│  │   Trigger: window.dispatchEvent(new CustomEvent("open-asset-picker"))│
│  └────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘

★ = DAM-contributed
```

---

### 10.4. `DAMHooks` — Complete `hooks.py` Reference

```python
# src/modules/dam/hooks.py
from src.core.hooks import hookimpl
from src.ui.registry import ui_registry, AppMetadata
from src.ui.admin_registry import admin_registry, AdminWidget
from src.ui.layout import ui_slots

class DAMHooks:
    module_name = "dam"

    # ── Models / Routes ───────────────────────────────────────────────
    @hookimpl
    def register_models(self):
        from .models import Asset, Link, Album
        return [Asset, Link, Album]

    @hookimpl
    def register_routes(self, app):
        from .router import router
        app.include_router(router)

    # ── UI Surfaces ────────────────────────────────────────────────────
    @hookimpl
    def register_page_slots(self, registry):
        """Declare injectable slots in DAM pages for other modules."""
        registry.declare("/dam/assets/{id}", "details_panel")    # e.g. Blogger adds a "Used In Posts" tab
        registry.declare("/dam/assets/{id}", "actions_toolbar")  # e.g. Editor adds "Edit in Canva" button

    @hookimpl
    def register_ui(self):
        # 1. Launchpad card + sidebar link + command palette entries
        ui_registry.register_app(AppMetadata(
            name="Media Library",
            icon="photo_library",
            route="/dam",
            description="Upload, search, and manage all digital assets.",
            category="Content",
            commands=["upload asset", "search images", "find similar",
                      "browse files", "view albums", "open graph explorer"],
            keyboard_shortcut="Alt+D",
        ))
        # 2. Quick Upload button in header (always visible)
        from .ui.components import dam_quick_upload_button
        ui_slots.add("header", dam_quick_upload_button, module="dam")

        # 3. Storage overview mini-widget on home dashboard
        from .ui.components import dam_storage_widget
        ui_slots.add("dashboard_widgets", dam_storage_widget, module="dam")

        # 4. Global Asset Picker overlay — other modules open via JS event
        from .ui.components import dam_asset_picker_overlay
        ui_slots.add("asset_picker_overlay", dam_asset_picker_overlay, module="dam")

        # 5. Register all DAM NiceGUI pages
        from . import ui as _dam_ui  # noqa: triggers @ui.page() decorators

    @hookimpl
    def register_admin_widgets(self):
        """Pipeline health widget on /admin dashboard."""
        from .ui.admin_widget import DAMAdminWidget
        admin_registry.register_widget(AdminWidget(
            name="Media Library",
            component=DAMAdminWidget,
            icon="photo_library",
            description="Asset counts, vector coverage, pipeline health.",
            column_span=2,
        ))

    # ── Settings ───────────────────────────────────────────────────────
    @hookimpl
    def register_settings(self):
        from .settings import DAMSettings
        return DAMSettings

    # ── Phase 0 service hooks (detailed in §9) ─────────────────────────
    @hookimpl
    def register_services(self): ...
    @hookimpl
    async def on_startup_async(self): ...
    @hookimpl
    def register_pipeline_processors(self): ...
    @hookimpl
    def register_asset_drivers(self): ...
    @hookimpl
    def register_asset_types(self): ...
    @hookimpl
    def register_vector_definitions(self): ...

hooks = DAMHooks()
```

---

### 10.5. `DAMSettings` — Expanded Persistent Settings Model

Replaces the minimal model in §9.7. All fields are editable live in `/admin/settings` with no extra code — `DataExplorer` auto-generates the form from the Pydantic schema.

```python
# src/modules/dam/settings.py
from pydantic import BaseModel, Field
from typing import List, Optional

class DAMSettings(BaseModel):
    """
    Persistent DAM settings — stored in MongoDB system_settings collection.
    Editable in /admin/settings. Env vars in config.py provide first-boot defaults.
    """
    # ── Gallery UI ──────────────────────────────────────────────────────
    default_gallery_columns:  int   = Field(4, ge=1, le=8,   description="Grid columns in /dam gallery")
    default_sort:             str   = Field("created_desc",   description="created_desc | created_asc | size_desc | filename_asc | relevance")
    default_page_size:        int   = Field(30, ge=10, le=200)
    show_ai_captions:         bool  = Field(True,  description="Show AI captions under gallery card thumbnails")
    show_ai_tags:             bool  = Field(True,  description="Show AI tag chips on gallery cards")
    show_score_pills:         bool  = Field(True,  description="Show RRF relevance score pill on search result cards")

    # ── Upload ──────────────────────────────────────────────────────────
    max_upload_size_mb:       int   = Field(100, ge=1, le=10000, description="Max file size per upload in MB")
    allowed_mime_types:       List[str] = Field(
        default_factory=lambda: ["image/*", "video/*", "audio/*", "application/pdf"],
        description="Accepted MIME types (glob patterns). e.g. ['image/*', 'video/mp4']"
    )
    auto_analyze_on_upload:   bool  = Field(True,  description="Run full AI pipeline immediately after upload")
    default_visibility:       str   = Field("private", description="Default visibility: private | public | shared")

    # ── AI Features ─────────────────────────────────────────────────────
    ai_enabled:               bool  = Field(False, description="Enable AI pipeline (BLIP, CLIP, MobileNet). Requires GPU recommended.")
    tagger_threshold:         float = Field(0.35, ge=0.0, le=1.0, description="Min confidence to include an AI tag")
    detection_threshold:      float = Field(0.50, ge=0.0, le=1.0, description="Min confidence to include a detected object")
    vector_relation_threshold:float = Field(0.85, ge=0.0, le=1.0, description="Min similarity score to create visually_similar_to link")
    blip_max_new_tokens:      int   = Field(50, ge=10, le=200,     description="Max BLIP caption length in tokens")
    auto_create_relations:    bool  = Field(True,  description="Automatically create visually_similar_to links after vector indexing")

    # ── Search ──────────────────────────────────────────────────────────
    search_default_limit:     int   = Field(30, ge=1, le=200)
    graph_expand_by_default:  bool  = Field(False, description="Auto-expand graph relations in search results")

    # ── Watcher ─────────────────────────────────────────────────────────
    watch_enabled:            bool  = Field(True,  description="Enable filesystem watcher for auto-sync (requires on_startup_async)")
    watch_paths:              List[str] = Field(default_factory=list, description="Absolute paths to watch (overridden by DAM_WATCH_PATHS env var if set)")
    cache_dir:                str   = Field("data/dam_cache", description="Local directory for generated thumbnails and derivatives")
    thumbnail_sizes:          List[int] = Field(default_factory=lambda: [200, 800, 1920], description="Thumbnail width breakpoints in px")

    class Config:
        title = "DAM Module Settings"
```

---

### 10.6. DAM UI Pages

All pages live in `src/modules/dam/ui/` and are registered by `DAMHooks.register_ui()`.

| Route | File | Key Features |
|-------|------|--------------|
| `/dam` | `gallery.py` | Grid/list toggle, search bar, filter sidebar with live facet counts, infinite scroll, drag & drop upload, multi-select bulk actions |
| `/dam/assets/{id}` | `viewer.py` | Full preview, EXIF/AI metadata tabs, bbox overlay on detections, graph mini-view, injectable `details_panel` + `actions_toolbar` slots |
| `/dam/search` | `search.py` | Full-screen hybrid search (text + image upload), `matched_by` pills, facet sidebar |
| `/dam/albums` | `albums.py` | Album CRUD list |
| `/dam/albums/{id}` | `albums.py` | Album asset grid with internal search |
| `/dam/graph` | `graph.py` | Cytoscape.js full knowledge graph, click-to-expand, breadcrumb trail |

#### `dam_quick_upload_button` (header slot)

```python
# src/modules/dam/ui/components.py

def dam_quick_upload_button():
    """Injected into the header bar. Opens the upload dropzone dialog."""
    btn = ui.button(icon="upload", on_click=lambda: upload_dialog.open()).props("flat round color=primary")
    btn.tooltip("Upload to Media Library")
    # Upload dialog defined with ui.dialog() + ui.upload() dropzone
```

#### `dam_storage_widget` (dashboard_widgets slot)

```python
def dam_storage_widget():
    """Mini overview card on the home dashboard."""
    with ui.card().classes("min-w-64"):
        with ui.row().classes("items-center gap-2 mb-2"):
            ui.icon("photo_library").classes("text-primary")
            ui.label("Media Library").classes("font-bold")
        # Fetched async from GET /api/dam/pipeline/status
        ui.label("Loading…").bind_text_from(dam_stats, "summary")
        ui.button("Open Gallery", on_click=lambda: ui.navigate.to("/dam")).props("flat size=sm")
```

#### `dam_asset_picker_overlay` (asset_picker_overlay slot)

Allows any other module to open the Asset Picker without a page navigation.

```python
# Trigger from any module's NiceGUI page:
# ui.run_javascript("window.dispatchEvent(new CustomEvent('open-asset-picker', {detail: {callback_id: 'field_123', types: ['image']}}))")

def dam_asset_picker_overlay():
    """Global modal — rendered once in layout, shown/hidden via JS events."""
    with ui.dialog() as picker_dialog:
        with ui.card().classes("w-full max-w-4xl h-[70vh]"):
            ui.label("Select Asset").classes("text-xl font-bold mb-4")
            # Embedded mini-gallery with search
            # On selection: run_javascript("window.dispatchEvent(new CustomEvent('asset-selected', {detail: {callback_id, asset}}))")
    
    ui.run_javascript("""
        window.addEventListener('open-asset-picker', (e) => {
            // Signal NiceGUI to open dialog
        });
    """)
```

#### `DAMAdminWidget` (/admin widget, colspan=2)

```
┌─[photo_library]  Media Library ──────────────────────────────────────┐
│  Total: 1,204  │  Ready: 1,180  │  Processing: 14  │  Error: 10       │
│  ─────────────────────────────────────────────────────────────────── │
│  Vector Coverage:  CLIP ████████░░ 82%   MobileNet ██████░░ 75%       │
│  AI Captions:      ████████████░ 92%  |  AI Tags: ████████░ 80%       │
│  ─────────────────────────────────────────────────────────────────── │
│  [View Pipeline Status →]   [Reprocess Errors →]   [Open Gallery →]   │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 10.7. Phase 0 Summary — Updated File Checklist

| File | Action | Purpose |
|------|--------|---------|
| `src/core/hooks.py` | +7 hookspecs | `register_services`, `on_startup_async`, `register_pipeline_processors`, `register_asset_drivers`, `register_asset_types`, `register_vector_definitions`, **`register_page_slots`** |
| `src/core/module_loader.py` | +2 methods | `register_module_services()` lifecycle step, `register_page_slots()` call before `register_ui()` |
| `src/core/config.py` | +env vars | Qdrant + DAM env vars |
| `src/main.py` | +async lifespan steps | Await `on_startup_async`, call `register_module_services()` |
| `src/core/registry.py` | +2 methods | `register_named()`, `get_named()` |
| `src/core/services/settings_service.py` | +1 method | `get_typed(name, Schema) → T` |
| `src/ui/layout.py` | Modify `UI_Slot` | Open slot registration + `asset_picker_overlay` + `command_palette_actions` builtins |
| `src/ui/registry.py` | Modify `AppMetadata` | Add `badge_text`, `keyboard_shortcut` |
| `src/ui/page_slot_registry.py` | **NEW** | `PageSlotRegistry`, `PageSlot`, singleton |
| `src/modules/dam/hooks.py` | **NEW** | `DAMHooks` — all 13 hookspec implementations |
| `src/modules/dam/settings.py` | **NEW** | `DAMSettings` — 20 editable fields |
| `src/modules/dam/ui/` | **NEW** | Gallery, Viewer, Search, Albums, Graph, Admin widget, components |
