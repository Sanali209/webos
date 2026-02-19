# Digital Asset Management (DAM) Module Design

## 1. Overview
The **DAM Module** acts as a **Transparent Indexer** and "Knowledge Base" layer over your existing file system (NAS/Local). It does **not** move or rename your files. Instead, it indexes them, extracts rich metadata, and builds a graph of relationships, treating the disk as the single source of truth.

## 2. Architecture
The module follows the standard WebOS architecture:
- **Backend**: FastAPI Router + Services.
- **Data**: MongoDB (Metadata/Graph) + **Existing File System** (Binary Content).
- **Sidecar Storage**: `.cache` or System folder for thumbnails/previews.
- **Frontend**: NiceGUI Components (Gallery, Upload, Lightbox).

### 2.1. Relationship with Storage Module
The `dam` module uses `storage` for **read-only access** to originals and **write access** to the Sidecar/Cache.
- `storage` handles: Raw I/O, File Listing.
- `dam` handles: Indexing, Metadata, Search, Graph.

## 3. Data Models

### 3.1. `Asset` (CoreDocument)
The primary entity representing a managed file.

```python
class AssetType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    OTHER = "other"
    # Virtual Types
    URL = "url"
    COLLECTION = "collection"
    LOG_ENTRY = "log_entry"
    PROXY = "proxy"
    # Composite Types
    REGION = "region"        # Bounding box on image
    APP_PACKAGE = "app_package" # Installer + License + Icon
    TEXTURE_PACK = "texture_pack" # ZIP archive transparently indexed

class AssetCategory(str, Enum):
    PHYSICAL = "physical"   # File in CAS
    VIRTUAL = "virtual"     # Metadata/Link only
    COMPOSITE = "composite" # Group of assets (Bundle)

class AssetStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

class Asset(CoreDocument, OwnedDocument):
    # Core File Info
    filename: str
    size: Optional[int]  # Optional for virtual
    mime_type: Optional[str] # Optional for virtual
    is_virtual: bool = False # Flag for virtual assets
    
    status: AssetStatus = AssetStatus.UPLOADING
    error_message: Optional[str]
    visibility: str = "private" # private, shared, public
    
    # Storage
    # Physical: "fs://s3/assets/..."
    # Virtual: "virtual://url", "virtual://collection", etc.
    storage_urn: str
    
    hash: Optional[str]  # SHA-256 (Physical only)
    phash: Optional[str]  # Perceptual Hash
    
    # Classification
    asset_type: AssetType
    tags: List[str] = []
    
    # Visuals
    thumbnail_urn: Optional[str]
    # Pyramid: {"small": "...", "medium": "...", "large": "..."}
    thumbnails: Dict[str, str] = {}
    width: Optional[int]
    height: Optional[int]
    duration: Optional[float]
    
    # Metadata
    title: Optional[str]
    description: Optional[str]
    
    # Extended Metadata (Schema-less)
    # Core Schemas: "exif", "iptc", "xmp"
    # Module Schemas: "web_scraper" (source_url), "gallery" (rating)
    metadata: Dict[str, Any] = {}
    
    # Versioning (Optional V2)
    version: int = 1

### 3.3. Graph Architecture (The "Knowledge Base" Layer)
Instead of embedding all relations, we use a dedicated **Adjacency List** collection to model the system as a Graph.

```python
class Link(Document):
    """
    Represents a directed edge in the Knowledge Graph.
    Source -> [Relation] -> Target
    """
    source_id: PydanticObjectId
    source_type: str  # "Asset", "User", "Project", "Machine"
    
    target_id: PydanticObjectId
    target_type: str
    
    relation: str  # e.g., "contains", "transformed_to", "visually_similar_to"
    weight: float = 1.0
    metadata: Dict[str, Any] = {}
```

#### Semantic Relation Types
1.  **Hierarchical**: `contains` (Folder->Asset), `includes` (Album->Asset), `owns` (Project->Document).
2.  **Derivative**: `transformed_to` (Raw->Jpg), `extracted_from` (Text->Pdf), `downloaded_by` (Asset->Scraper).
3.  **Associative**: `visually_similar_to` (pHash), `depicts` (Photo->User), `related_to` (Drawing->Part).

    # Metadata (Layer 3: Namespaced)
    # e.g., "exif": {...}, "geo": {...}, "web_scraper": {...}
    metadata: Dict[str, Any] = {}
    
    # Layer 4: Contextual (Graph) -> See Link Model
    
    # Versioning
    version: int = 1

### 3.2. Layered Metadata Architecture
We move away from flat columns to a 4-layer structure:

1.  **Core (System)**: Fixed fields (`sha256`, `asset_type`, `status`, `visibility`).
2.  **Technical (Auto)**: Extracted data (`width`, `duration`, `file_size`).
3.  **Namespaced (Modular)**: Dictionary `metadata` where keys are Module IDs.
    -   `metadata["exif"]`: Camera data.
    -   `metadata["geo"]`: GPS coordinates.
    -   `metadata["web_scraper"]`: Source URL, PageRank.
4.  **Contextual (Graph)**: Relations via `Link` collection (`derived_from`, `belongs_to`).

#### Metadata Registry (Schema-on-Read)
Drivers and Modules register **Pydantic Schemas** to validate/type-hint their namespaces.

```python
class AssetSDK:
    def get_metadata(self, asset: Asset, namespace: str, schema: Type[T]) -> T:
        data = asset.metadata.get(namespace, {})
        return schema(**data)
```

class Album(CoreDocument, OwnedDocument):
    """
    Virtual collection of assets (Project / Folder).
    Does not copy files, just references them.
    """
    name: str
    description: Optional[str]
    # Assets in this album (ordered list of IDs)
    assets: List[Link[Asset]] = []
    # Parent album for nested structure (optional)
    parent_id: Optional[PydanticObjectId]
    cover_image: Optional[Link[Asset]]
```

## 4. Components

### 4.1. `AssetService` (The Transparent Indexer)
This service registers existing files and syncs metadata without altering the originals.

#### 4.1.1. Ingestion / Indexing Phase
**A. Physical Files (`register_path`)**:
1.  **Registration**:
    -   Input: Absolute Path (e.g., `/mnt/nas/photos/img.jpg`).
    -   Action: Create/Update `Asset` with `storage_urn="fs://local/mnt/nas/photos/img.jpg"`.
    -   **Source of Truth**: The File System.
2.  **Fingerprinting (Background)**:
    -   Calculate SHA-256 for **Logical Deduplication** (finding duplicates across folders).
    -   Store `hash` in DB.
3.  **Sidecar Generation**:
    -   Trigger Thumbnail/Preview generation.
    -   Save to `fs://system/dam_cache/{hash}/thumb.webp`.

**B. Virtual Assets (`ingest_virtual`)**:
-   **Input**: `AssetType` (e.g., URL), `data` (dict).
-   **Action**: Create `Asset(is_virtual=True, storage_urn="virtual://...", metadata=data)`.
-   **Trigger**: Start specialized pipeline (e.g., Scraper).

#### 4.1.2. Analysis Phase (Async)

#### 4.1.2. Analysis Phase (Async)
- **MimeType Detection**: Strict validation using `python-magic`.
    -   **Optimization**: Use Singleton instance to avoid reloading DB.
- **Metadata Extraction**:
    - **Images**: `ExifTool` via wrapper.
    - **Video**: `ffmpeg` probe.
- **Visual Hashing**: `pHash` calculation for similarity search.

#### 4.1.3. Derivative Generation (Async)
- **Thumbnails**: Pyramid generation (small/medium/large).
- **Transcoding**: Convert non-web formats (TIFF, MOV) to web-friendly (WebP, MP4).
- **OCR**: Text extraction for documents.

### 4.2. `ThumbnailGenerator`
- **Functionality**: Generates a **Pyramid of Previews** for performance.
    - `small` (200px): for Grid View.
    - `medium` (800px): for Quick Preview.
    - `large` (1920px): for Full Screen / Lightbox.
- **Implementation**: Uses `Pillow` (Images) and `ffmpeg` (Video frames).
- **Storage**: Thumbnails stored in local cache or S3 sidecar path.

### 4.3. `MetadataExtractor`
- Extracts EXIF, IPTC, and XMP data from uploaded files to populate the `metadata` field.

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

### 4.5. `FileWatcher` (The Core Synchronizer)
Since the FS is the source of truth, `FileWatcher` is critical for keeping the DB in sync.

-   **Mechanism**: Uses `watchdog` to monitor mounted paths.
-   **Events**:
    -   `on_created`: Calls `AssetService.register_path(path)`.
    -   `on_moved` (Rename): Updates `storage_urn` in DB. Preserves ID and Relations.
    -   `on_deleted`: Marks Asset `status=MISSING` (Soft Delete).
    -   `on_modified`: Triggers re-hashing and metadata update (debounced).
-   **Scavenger Task**:
    -   Periodic scan to catch up on missed events (e.g., if app was down).
    -   Verifies existence of all `PHYSICAL` assets.

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
Instead of hardcoded types, we use a **Strategy Pattern** with Drivers.

#### Architecture
```python
class BaseAssetDriver(ABC):
    asset_type: AssetType
    category: AssetCategory

    @abstractmethod
    async def on_ingest(self, asset: Asset, source_data: Any):
        """Primary ingestion logic (save file / create links)"""

    @abstractmethod
    async def get_preview_logic(self, asset: Asset):
        """How to generate thumbnail (crop / screenshot / icon)"""

    @abstractmethod
    def render_ui_component(self, asset: Asset):
        """NiceGUI component for Shell/Gallery"""
```

#### Specific Drivers
1.  **`RegionDriver`** (Virtual -> Composite):
    -   *Ingest*: Saves `bbox` and `parent_id` to metadata. Does not create files.
    -   *Pipeline*: Triggers crop generation from parent image for `thumbnail_urn`.
    -   *UI*: Gallery shows crop; click opens parent with highlighted region.
2.  **`AppPackageDriver`** (Composite):
    -   *Ingest*: Parses `.exe` resources. Creates `PHYSICAL` assets for components (Installer, License, Icon).
    -   *Graph*: Creates `contains` link to components.
    -   *UI*: Install card with version info and "Install" action (TaskIQ).
3.  **`TexturePackDriver`** (Physical -> Composite):
    -   *Ingest*: Index ZIP contents (filenames, sizes) into `metadata`.
    -   *Pipeline*: Extract primary texture (e.g., `diffuse.png`) for preview.
    -   *UI*: Virtual Folder view of ZIP contents without full extraction.
    -   *Subtypes*: `invoice`, `contract`, `tech_spec` (via `metadata.sub_type`).
    -   *Ingest*: 
        -   If Physical: OCR & Text Extraction.
        -   If Virtual: Parse JSON/API data.
    -   *Preview*: Synthetic HTML card (e.g., displaying Invoice Amount & Status).
    -   *Graph*: Links to entities (`signed_by` User, `version_of` File).

### 4.9. `AssetDriverManager`
-   Registry that maps `AssetType` -> `Driver`.
-   `AssetService` delegates to this manager during ingestion.

```python
class AssetDriverManager:
    def __init__(self):
        self._drivers: Dict[AssetType, BaseAssetDriver] = {}

    def register_driver(self, driver: BaseAssetDriver):
        self._drivers[driver.asset_type] = driver

    async def process_asset(self, asset: Asset):
        driver = self._drivers.get(asset.asset_type)
        if driver:
            await driver.on_ingest(asset)
```
-   `AssetService` delegates to this manager during ingestion.

## 5. UI Implementation (NiceGUI)

### 5.1. `AssetGallery`
- A responsive grid view of asset thumbnails.
- **Features**:
    - Infinite scroll or pagination.
    - Drag & Drop upload zone.
    - Sidebar filters (Type, Date, Tags).
    - Multi-select for bulk actions (Delete, Tag).

### 5.2. `AssetViewer` (Lightbox)
- Modal dialog for viewing the full-size asset.
- **Inspector Sidebar** (Layered Tabs):
    -   **General**: Core + Technical info.
    -   **Modules**: Dynamic tabs for each Namespace (Visualized via DataExplorer).
    -   **Graph**: Visualizes immediate neighbors (`Graph SDK`).
- "Copy Link" / "Download" actions.

### 5.3. `GraphExplorer` (New)
- **Visualization**: Interactive node-link diagram using **Cytoscape.js** or **D3.js**.
- **Navigation**: Click node to expand neighbors.
- **Breadcrumbs 2.0**: Path-based navigation (e.g., `Project X > contains > Folder Y > includes > Asset Z`).

### 5.3. `AssetPicker` (Widget)
- A reusable component that other modules (e.g., Blog, Page Builder) can open to select an asset.
- Returns the `Asset` object or public URL.

## 6. API Endpoints
- `POST /api/dam/upload`: Multipart upload.
- `GET /api/dam/assets`: List with filters.
- `GET /api/dam/assets/{id}`: Detail view.
- `PATCH /api/dam/assets/{id}`: Update metadata.
- `DELETE /api/dam/assets/{id}`: Delete (Soft or Hard).

## 7. Roadmap
- [ ] **Phase 1**: Basic Upload, Storage (AFS), and Gallery View.
- [ ] **Phase 2**: Thumbnail Generation & Metadata Extraction.
- [ ] **Phase 3**: Image Editor (Crop/Rotate) & Asset Picker Widget.
- [ ] **Phase 4**: Large File Support (TUS Protocol, Chunked Uploads).
