# DAM Module Roadmap
**Design Reference**: `des_docs/design/dam/dam_design.md`
**Companion Doc**: `des_docs/roadmap.md` (framework phases 0–10)
**Backlog**: [`des_docs/backlog.md`](file:///d:/github/webos/des_docs/backlog.md) — Phases 11–20

Each phase maps directly to the corresponding section in `dam_design.md`.
All phases run in strict sequence — each phase is a prerequisite for the next.

---

## Progress Tracking Workflow

This roadmap and `backlog.md` are kept in sync. Use the following workflow:

### When starting a subtask
1. Find the subtask here (e.g. `### 3.2 — 5 built-in type implementations`).
2. Open `backlog.md` → locate the matching phase (`## Phase 13: DAM — Asset Type System`).
3. Tick the corresponding backlog item with `[x]` as you complete it.

### When finishing a phase
1. Confirm **all** `- [ ]` items in `backlog.md` for that phase are `[x]`.
2. Confirm the **Regression** and **Self-check** items in this roadmap pass.
3. Add an entry to the **DAM Knowledge Log** section at the bottom of `backlog.md` with:
   - Date, phase number
   - Any bugs, gotchas, or decisions made during implementation
   - Actual benchmark numbers (e.g. AI pipeline CPU time)
4. Move to the next phase.

### Backlog ↔ Roadmap cross-reference

| Backlog phase | Roadmap phase | Covers |
|---------------|---------------|--------|
| Phase 11 | DAM Phase 1 | Framework Preparation |
| Phase 12 | DAM Phase 2 | Asset Model |
| Phase 13 | DAM Phase 3 | Asset Type System |
| Phase 14 | DAM Phase 4 | Asset Drivers |
| Phase 15 | DAM Phase 5 | Core Services |
| Phase 16 | DAM Phase 6 | Vector Service |
| Phase 17 | DAM Phase 7 | AI Processing Pipeline |
| Phase 18 | DAM Phase 8 | Search & Discovery |
| Phase 19 | DAM Phase 9 | API Layer |
| Phase 20 | DAM Phase 10 | UI & Integration |

---


## DAM Phase 1: Framework Preparation
**Maps to**: `dam_design.md §9 (Phase 0 Hookspecs) + §10 (UI & Settings Integration)`
**Goal**: Extend the WebOS *core* framework with all hooks, infrastructure changes, and UI system enhancements the DAM module needs. Zero DAM business logic here — only changes to `src/core/` and `src/ui/`.

### 1.1 — Add Qdrant to `docker-compose.yml`
- **Action**: Add `qdrant/qdrant:v1.9.2` service, REST `:6333`, gRPC `:6334`, `qdrant_data` volume. ✅ Done.
- **Goal**: `docker-compose up -d qdrant` persists data between container restarts.
- **Test**: `curl http://localhost:6333/healthz` → `{"title":"qdrant - healthy"}`.
- **Degradation**: Stop Qdrant. Verify WebOS still boots, non-vector endpoints respond normally.
- **Knowledge**: Pin version to `v1.9.2`; newer versions may change gRPC port env-var name.

### 1.2 — DAM env vars in `src/core/config.py`
- **Action**: Add `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION`, `DAM_WATCH_PATHS`, `DAM_CACHE_DIR`, `DAM_AI_ENABLED`, `DAM_TAGGER_THRESHOLD`, `DAM_DETECTION_THRESHOLD`, `DAM_VECTOR_RELATION_THRESHOLD` with safe defaults.
- **Goal**: All DAM services get type-safe config at import time; app starts with no `.env` DAM block.
- **Test**: Override `QDRANT_URL=http://test:6333` in test env; assert `settings.QDRANT_URL == "http://test:6333"`.
- **Test**: Import `src.core.config` with no `.env` → no `ValidationError`.

### 1.3 — Seven new hookspecs in `src/core/hooks.py`
- **Action**: Add `register_services`, `on_startup_async`, `register_pipeline_processors`, `register_asset_drivers`, `register_asset_types`, `register_vector_definitions`, `register_page_slots` to `WebOSHookSpec`.
- **Goal**: `loader.pm.hook` has all seven attributes; calling them with no implementations returns empty list without error.
- **Test**: `assert hasattr(loader.pm.hook, "on_startup_async")`. Assert calling it with zero impls returns `[]`.
- **Degradation**: Module implementing none of the new hooks — startup still completes in < 5 s.
- **Knowledge**: `on_startup_async` must NOT use `firstresult=True`; all modules must get to run it.

### 1.4 — Wire new hooks in `src/core/module_loader.py`
- **Action**: Add `register_module_services()`, `trigger_startup_async()`, `register_all_page_slots()`. Update `main.py` lifespan: call `trigger_startup_async()` after `init_db`.
- **Goal**: Dispatch order: `discover → models → routes → services → page_slots → ui → on_startup_async`.
- **Test**: Test module with `on_startup_async` that sets a flag. Assert flag set after lifespan starts.
- **Degradation**: Exception inside one module's `on_startup_async`. Assert error logged; other modules still start.

### 1.5 — Open slot registration in `src/ui/layout.py` (`UI_Slot`)
- **Action**: Remove hardcoded-4-slots guard. Accept any slot name. Add `module` kwarg to `add()`. Add `asset_picker_overlay` and `command_palette_actions` to default slot dict. Render `asset_picker_overlay` once at bottom of shell `__enter__`.
- **Goal**: `ui_slots.add("asset_picker_overlay", fn, module="dam")` registers without warning.
- **Test**: Add builder to `"custom_test_slot"`. Assert `ui_slots.render("custom_test_slot")` calls builder.

### 1.6 — Create `src/ui/page_slot_registry.py`
- **Action**: Implement `PageSlot` dataclass, `PageSlotRegistry` with `declare(path, slot_name)`, `inject(path, slot_name, builder)`, `render(path, slot_name, **kwargs)`. Singleton `page_slot_registry`.
- **Goal**: Modules declare injectable slots on their pages; other modules fill them without coupling.
- **Test**: `registry.declare("/dam/assets/{id}", "details_panel")`. Inject a builder. `render(...)` calls it once.
- **Degradation**: `inject` into undeclared slot → log warning, no exception.

### 1.7 — Enhance `AppMetadata` in `src/ui/registry.py`
- **Action**: Add `badge_text: Optional[str] = None` and `keyboard_shortcut: Optional[str] = None`. Update launchpad card renderer to show badge chip when set.
- **Test**: Register app with `badge_text="1,204 assets"`. Assert chip visible in rendered output.

### 1.8 — `get_typed()` in `src/core/services/settings_service.py`
- **Action**: Add `get_typed(module_name: str, schema_class: Type[T]) -> T` with `KeyError`/`TypeError` guards.
- **Test**: Register and load `VaultSettings`. `get_typed("vault", VaultSettings)` returns correct type. Wrong type → `TypeError`.

### Phase 1 Completion
- [ ] **Regression**: Full test suite — admin, vault, blogger modules unaffected. Startup time increase < 200 ms vs baseline.
- [ ] **Backlog update**: Mark Phase 1 items in `des_docs/backlog.md`.
- [ ] **Knowledge capture**: Qdrant version pin, hook dispatch order, `on_startup_async` isolation pattern.
- [ ] **Self-check**: `python main.py modules list` succeeds. `curl /health` → 200. `curl http://localhost:6333/healthz` → healthy.

---

## DAM Phase 2: Asset Model
**Maps to**: `dam_design.md §1`
**Goal**: Create the `src/modules/dam/` package skeleton and all Beanie persistence models. No business logic — purely structural.

### 2.1 — Module package skeleton
- **Action**: Create `src/modules/dam/__init__.py`, `hooks.py` (stub `DAMHooks`), `settings.py` (stub `DAMSettings`), `models.py`, `router.py` (empty), `schemas/`, `services/`, `processors/`, `drivers/`, `ui/`.
- **Goal**: `python main.py modules list` shows `src.modules.dam` with zero errors.
- **Test**: `import src.modules.dam` succeeds. `loader.loaded_modules` contains `"src.modules.dam"`.

### 2.2 — `Asset` Beanie model
- **Action**: Implement `Asset(CoreDocument)` with fields: `filename`, `title`, `description`, `storage_urn`, `asset_types: List[str]`, `primary_type: str`, `tags`, `ai_tags`, `ai_caption`, `confidence_scores: Dict[str,float]`, `detected_objects: List[DetectedObject]`, `vectors: Dict[str,List[float]]`, `hash`, `phash`, `file_size`, `mime_type`, `status` (Enum: pending/processing/ready/error/partial), `visibility`, `metadata: Dict[str,Any]`. Add compound text index on `filename + title + description + tags + ai_tags + ai_caption`.
- **Goal**: Asset registers with Beanie on startup; text index created in MongoDB.
- **Test**: Create `Asset(filename="test.jpg", storage_urn="fs://local/dam/test.jpg", asset_types=["image"], primary_type="image")`. Assert `created_at` populated. Text index exists: `db.dam_assets.getIndexes()`.
- **Degradation**: Insert Asset with only required fields → no `ValidationError`.

### 2.3 — `DetectedObject` sub-model
- **Action**: `DetectedObject(BaseModel)` with `class_name`, `subclass`, `confidence: float`, `bbox_x/y/w/h: float` (0–1 normalized).
- **Test**: Valid instance created. `confidence=1.5` → `ValidationError`.

### 2.4 — `Link` Beanie model
- **Action**: `Link(CoreDocument)` with `source_id`, `target_id: PydanticObjectId`, `relation: str`, `weight: float = 1.0`. Indexes on `(source_id, relation)` and `(target_id, relation)`.
- **Test**: Create two assets + one link. Fetch link by `source_id` → returns exactly 1 result.

### 2.5 — `Album` Beanie model
- **Action**: `Album(OwnedDocument)` with `title`, `description`, `cover_asset_id: Optional[PydanticObjectId]`, `asset_ids: List[PydanticObjectId] = []`. Index on `owner_id`.
- **Test**: User A album invisible to User B (OwnedDocument isolation verified).

### Phase 2 Completion
- [ ] **Regression**: Phase 1 tests pass. Admin/Vault modules unaffected.
- [ ] **Backlog update**: Mark Phase 2 items.
- [ ] **Knowledge capture**: Beanie text-index syntax (list of index tuples in `Settings.indexes`); `OwnedDocument` gives free user-scoped queries on Album.
- [ ] **Self-check**: App starts. MongoDB has `dam_assets`, `dam_links`, `dam_albums` collections with correct indexes visible in Compass.

---

## DAM Phase 3: Asset Type System
**Maps to**: `dam_design.md §2`
**Goal**: Implement `AssetTypeRegistry` and 5 built-in type definitions (image, video, audio, document, url). This registry drives thumbnail strategy, driver selection, and pipeline skip logic.

### 3.1 — `AssetTypeDefinition` base class
- **Action**: `AssetTypeDefinition(ABC)` with `type_id: str`, `accepted_mimes: List[str]`, `can_handle(mime) -> bool`, `describe() -> str`. `GenericAssetType` as fallback (returns `True` for any MIME).
- **Test**: `ImageAssetType().can_handle("image/jpeg")` → `True`. `ImageAssetType().can_handle("video/mp4")` → `False`. `GenericAssetType().can_handle("application/x-unknown")` → `True`.

### 3.2 — 5 built-in type implementations
- **Action**: `ImageAssetType` (jpeg, png, webp, gif, tiff, bmp), `VideoAssetType` (mp4, avi, mov, mkv, webm), `AudioAssetType` (mp3, wav, flac, ogg, aac), `DocumentAssetType` (pdf, docx, xlsx, pptx, txt, md), `UrlAssetType` (text/uri-list).
- **Test**: Each type handles 3 representative MIMEs. No MIME ambiguity across types.

### 3.3 — `AssetTypeRegistry` singleton
- **Action**: `register(AssetTypeDefinition)`, `get_handler(mime) -> AssetTypeDefinition` (falls back to `GenericAssetType`), `all_types() -> List`.
- **Goal**: Hookspec `register_asset_types` fills registry before services start.
- **Test**: `registry.get_handler("image/jpeg").type_id == "image"`. `registry.get_handler("application/x-foo").type_id == "generic"`. `len(registry.all_types()) == 6` (5 + generic).
- **Degradation**: Duplicate `type_id` registration → log warning, keep first.

### 3.4 — `DAMHooks.register_asset_types`
- **Action**: Hookimpl returns the 5 built-in definitions. Module loader calls `register_asset_types` and populates registry.
- **Test**: After module load, `registry.get_handler("video/quicktime").type_id == "video"`.

### Phase 3 Completion
- [ ] **Regression**: Phases 1–2 pass. No core changes.
- [ ] **Backlog update**: Mark Phase 3 items.
- [ ] **Knowledge capture**: Use exact MIME strings (not glob patterns) in `accepted_mimes` for precision; `GenericAssetType` is the safety net.
- [ ] **Self-check**: `AssetTypeRegistry.get_handler("audio/flac").type_id == "audio"`.

---

## DAM Phase 4: Asset Drivers
**Maps to**: `dam_design.md §3`
**Goal**: Implement the driver layer — each driver extracts rich, type-specific metadata (EXIF, duration, codec, page count) from file bytes after ingestion.

### 4.1 — `BaseAssetDriver` abstract class
- **Action**: `BaseAssetDriver(ABC)` with `type_id: str`, `abstract extract_metadata(asset: Asset, file_bytes: bytes) -> Dict[str, Any]`.
- **Test**: Subclass returns `{"test": 1}`. `AssetDriverManager.process(asset)` writes it into `asset.metadata`.

### 4.2 — `ImageDriver`
- **Action**: Use Pillow. Extract: `width`, `height`, `color_space`, `bit_depth`, EXIF dict (`make`, `model`, `gps_lat`, `gps_lon`, `taken_at`). Apply `ImageOps.exif_transpose` for rotation.
- **Test**: 1920×1080 PNG → `metadata["width"] == 1920`, `metadata["color_space"] == "RGB"`. JPEG with GPS → `metadata["gps_lat"]` is float.
- **Degradation**: Corrupt image → returns `{"error": "corrupt image"}`, no exception.

### 4.3 — `VideoDriver`
- **Action**: Use `ffprobe` (subprocess, 10 s timeout). Extract: `duration_s`, `width`, `height`, `fps`, `codec`, `bitrate`, `has_audio`, `audio_codec`.
- **Test**: Short `.mp4` → `metadata["duration_s"] > 0`, `metadata["codec"]` non-empty.
- **Degradation**: `ffprobe` not in PATH → `{"error": "ffprobe not found"}`, clear log message.

### 4.4 — `AudioDriver`
- **Action**: Use `mutagen`. Extract: `duration_s`, `bitrate`, `sample_rate`, `channels`, `title`, `artist`, `album`, `track_number`.
- **Test**: MP3 with ID3 tags → `metadata["artist"]` matches tag. No tags → `None` values, no exception.

### 4.5 — `DocumentDriver`
- **Action**: Use `PyMuPDF` (fitz) for PDF: `page_count`, `title`, `author`, `word_count_estimate`. Use `python-docx` for `.docx`. Plain text: word count only.
- **Test**: 3-page PDF → `metadata["page_count"] == 3`. Encrypted PDF → `metadata["error"] = "encrypted"`.

### 4.6 — `AssetDriverManager`
- **Action**: `register(driver)`, `process(asset)` — dispatches by `asset.primary_type`, writes result to `asset.metadata`, saves doc.
- **Test**: PNG after `process()` → `asset.metadata` has `width`, `height`, `color_space`.
- **Degradation**: No driver for `primary_type` → metadata left empty, no exception.

### Phase 4 Completion
- [ ] **Regression**: Phases 1–3 pass.
- [ ] **Backlog update**: Mark Phase 4 items.
- [ ] **Knowledge capture**: `ffprobe` must be installed separately (document in README). Pillow import: `from PIL import Image, ImageOps`. PyMuPDF: `import fitz`.
- [ ] **Self-check**: Upload JPEG → `GET /api/dam/assets/{id}` → `metadata` contains `width`, `height`, GPS fields.

---

## DAM Phase 5: Core Services
**Maps to**: `dam_design.md §5.1, §5.2 (AssetService), §5.3 (ThumbnailGenerator), §5.5 (WatcherService)`
**Goal**: The three workhorses of the DAM: ingestion, thumbnail generation, and automatic filesystem watching. All storage goes through AFS. At end of this phase, `status="pending"` assets exist — AI enrichment comes in Phase 7.

### 5.1 — `AssetService.ingest()`
- **Action**: Accept `path_or_url` + `asset_types`, `tags`, `title`, `visibility`. Steps: read bytes, compute SHA-256 hash, check duplicate (`Asset.find_one(hash=hash)`), store file via AFS (`fs://local/dam/` or `fs://s3/dam/`), detect MIME (`python-magic`), set `primary_type` from `AssetTypeRegistry.get_handler(mime).type_id`, create `Asset` doc with `status="pending"`, emit `dam:asset:ingested` event.
- **Goal**: Same file ingested twice → only 1 Asset doc (dedup by hash).
- **Test**: Ingest `test.png`. Assert `Asset` exists with correct `hash`, `file_size`, `mime_type`, `storage_urn`. Ingest same file again → still 1 doc in DB.
- **Degradation**: AFS write fails (mock `IOError`) → `asset.status = "error"`, exception not propagated to caller.

### 5.2 — `AssetService.delete()`
- **Action**: Remove file from AFS. Delete all thumbnails from cache dir. Delete `Link` docs with `source_id` or `target_id`. Remove from all `Album.asset_ids`. Delete `Asset` doc. Remove Qdrant point (calls `VectorService.delete(asset.id)`, no-op if Phase 6 not loaded).
- **Test**: Ingest → delete. Assert AFS file gone, DB doc gone, Links gone.
- **Degradation**: AFS delete fails → log error, continue deleting DB record (don't leave orphan doc).

### 5.3 — `ThumbnailGenerator`
- **Action**: `generate(asset)` uses Pillow. Sizes from `DAMSettings.thumbnail_sizes` (default: `[200, 800, 1920]`). Save as `{cache_dir}/{asset_id}/{size}.webp`. Apply `exif_transpose`. Skip non-image types (return placeholder path). Handle animated GIFs (first frame only).
- **Test**: Ingest 1920×1080 JPEG. Assert 3 WebP files at expected paths. Each ≤ target width. Format is WebP.
- **Test**: Ingest JPEG with EXIF orientation=6. Assert thumbnail is correctly rotated (not sideways).
- **Degradation**: Corrupt PNG → `status="error"` on asset, no unhandled exception, log entry with asset ID.

### 5.4 — `DAMHooks.register_services` + wiring
- **Action**: `register_services` hookimpl instantiates `AssetService`, `ThumbnailGenerator`, `AssetDriverManager`, `WatcherService`. Registers them in `ServiceRegistry`. Subscribe `dam:asset:ingested` on EventBus → call `ThumbnailGenerator.generate` + `AssetDriverManager.process`.
- **Test**: After module load, `service_registry.get(AssetService)` returns instance. After `dam:asset:ingested` emitted, thumbnail files created within 3 s.

### 5.5 — `WatcherService`
- **Action**: Uses `watchdog` library. On `FileCreatedEvent` / `FileModifiedEvent` in watched paths from `DAMSettings.watch_paths`: call `AssetService.ingest()`. Start/stop via `on_startup_async` / `on_shutdown`.
- **Test**: Copy test image to watched tmp dir. Wait 3 s. Assert `Asset.find_one(filename="test.jpg")` not None.
- **Degradation**: Watch path does not exist → log warning, start without crash. Path created later → watcher re-scans on next poll cycle.
- **Notes**: Set `watch_enabled = False` in CI/test config to avoid filesystem side effects.

### Phase 5 Completion
- [ ] **Regression**: Phases 1–4 pass. Storage module (AFS) unaffected.
- [ ] **Backlog update**: Mark Phase 5 items.
- [ ] **Knowledge capture**: `python-magic` requires `libmagic` on Windows (install `python-magic-bin`). `watchdog` `Observer` must be stopped in `on_shutdown`. SHA-256 chunk-read pattern for large files.
- [ ] **Self-check**: Upload image via API. File appears in MinIO/local. Thumbnail exists at `{cache_dir}/{id}/200.webp`. `GET /api/dam/assets/{id}/thumbnail/200` → WebP bytes.

---

## DAM Phase 6: Vector Service
**Maps to**: `dam_design.md §5.4`
**Goal**: Build the Qdrant integration layer. At end of this phase, vectors can be indexed and retrieved — but no vectors are generated yet (AI pipeline in Phase 7).

### 6.1 — `VectorDefinition` model
- **Action**: Implement `VectorDefinition` dataclass: `name: str`, `size: int`, `distance: str` (Cosine/Dot/Euclid). DAM registers `clip_image` (512-d, Cosine) and `clip_text` (512-d, Cosine).
- **Test**: `VectorDefinition(name="clip_image", size=512, distance="Cosine")` → valid.

### 6.2 — `VectorService.__init__` + `ensure_collection`
- **Action**: On init: connect to Qdrant (`QDRANT_URL`), set `self._available = False` on connection error. `ensure_collection(definition)`: create Qdrant collection if not exists with `vectors_config` dict using `definition.size` and `definition.distance`. Called for each registered `VectorDefinition` in `on_startup_async`.
- **Test**: Call `ensure_collection(clip_image_def)`. Assert Qdrant has collection `clip_image`. Call again → no error (idempotent).
- **Degradation**: Qdrant unreachable → `self._available = False`, logs error, no exception.

### 6.3 — `VectorService.index()` and `delete()`
- **Action**: `index(asset_id: str, vec_name: str, vector: List[float])` → `client.upsert(collection_name=vec_name, points=[PointStruct(id=hash(asset_id), payload={"asset_id": asset_id}, vector=vector)])`. `delete(asset_id)` → `client.delete(collection_name=*, points_selector=...)` for all collections.
- **Test**: Index vector. Retrieve with `client.retrieve`. Assert payload `asset_id` matches.

### 6.4 — `VectorService.search()`
- **Action**: `search(vec_name, query_vector, limit, filter_payload) -> List[ScoredResult]`. Returns `[]` if `not self._available`. Filter maps `AssetFilter` fields to Qdrant `FieldCondition` objects.
- **Test**: Index 3 vectors. Search with one of them. Assert it's top result, score ≈ 1.0.
- **Degradation**: `vec_name` collection does not exist → return `[]`, log warning.

### 6.5 — `DAMHooks.register_vector_definitions`
- **Action**: Hookimpl returns `[clip_image_def, clip_text_def]`. Loader calls hook and passes results to `VectorService.ensure_collection` for each.
- **Test**: After module load `on_startup_async`, Qdrant has `clip_image` collection.

### Phase 6 Completion
- [ ] **Regression**: All Phases 1–5 pass. If Qdrant is down, app still starts (graceful degradation).
- [ ] **Backlog update**: Mark Phase 6 items.
- [ ] **Knowledge capture**: Qdrant ID must be `uint64` or UUID — use `abs(hash(str(asset_id))) % (2**63)` for ObjectId→int conversion. Qdrant `upsert` is idempotent. Qdrant payload filter `FieldCondition` syntax.
- [ ] **Self-check**: Start app with Qdrant running. `curl http://localhost:6333/collections` shows `clip_image` collection. Stop Qdrant → app boots without error.

---

## DAM Phase 7: AI Processing Pipeline
**Maps to**: `dam_design.md §6`
**Goal**: Build all AI enrichment processors (BLIP, CLIP, SmileWolf Tagger, MobileNet Detection, Vector Relations) and the `PipelineOrchestrator` that runs them as a TaskIQ background task triggered after ingestion.

### 7.1 — `BasePipelineProcessor` and `PipelineOrchestrator`
- **Action**: `BasePipelineProcessor(ABC)` with `name: str`, `applies_to: List[str]` (asset type IDs), `abstract process(asset: Asset) -> None`. `PipelineOrchestrator.run(asset_id)`: load asset, iterate processors in registration order, call `process(asset)` if asset type in `applies_to`, catch per-processor exceptions and store in `asset.metadata["pipeline_errors"]`, set `status="ready"` on success or `"partial"` if any processor errored.
- **Goal**: One processor crashing does not abort remaining processors.
- **Test**: Register 2 processors, second raises. Assert first ran, `status="partial"`, error logged.

### 7.2 — CLIP embedding processor (`processors/clip_processor.py`)
- **Action**: Load `sentence-transformers/clip-ViT-B-32` (or `openai/clip-vit-base-patch32`) with `@lru_cache`. `process(asset)`: load image bytes from AFS, encode to 512-d vector, call `VectorService.index(asset.id, "clip_image", vector)`, store in `asset.vectors["clip_image"]`. Gate: skip if `not settings.DAM_AI_ENABLED`.
- **Test**: Process sample image. Assert `len(asset.vectors["clip_image"]) == 512`. Assert Qdrant `clip_image` collection has 1 point for asset.
- **Degradation**: Corrupt image → `status="partial"` with error, does not crash orchestrator.
- **Knowledge**: Model lazy-loads on first call; add 1–5 s cold-start warning in logs.

### 7.3 — BLIP captioning processor (`processors/blip_processor.py`)
- **Action**: Load `Salesforce/blip-image-captioning-base`. `process(asset)`: encode image, generate caption up to `DAMSettings.blip_max_new_tokens` tokens, store in `asset.ai_caption`. Apply only to `applies_to=["image"]`.
- **Test**: Process photo of a cat. Assert `"cat"` in `asset.ai_caption.lower()`.
- **Degradation**: Non-image asset → early return (checks `asset.primary_type`).

### 7.4 — SmileWolf tagger processor (`processors/tagger_processor.py`)
- **Action**: Load WD14/DeepDanbooru model. Predict tags with score ≥ `DAMSettings.tagger_threshold`. Store tags in `asset.ai_tags`, scores in `asset.confidence_scores`. Applies to `["image"]`. See `integrate/smile wolf tager.md` for model source.
- **Test**: Process sample image. Assert ≥ 3 tags in `asset.ai_tags`. All scores ≥ `tagger_threshold`.
- **Degradation**: Model file missing → `ModelNotAvailableError` caught in orchestrator, processor skipped, error recorded in `pipeline_errors`.

### 7.5 — Object detection processor (`processors/detection_processor.py`)
- **Action**: Load MobileNet SSD or YOLOv5-nano. For each detection ≥ `DAMSettings.detection_threshold`: append `DetectedObject` to `asset.detected_objects` with bbox (0–1 normalized). Applies to `["image"]`.
- **Test**: Process test image with a known person. Assert entry with `class_name="person"` in `detected_objects`.
- **Test**: Blank white image → `detected_objects == []`.

### 7.6 — Vector relation creator (`processors/vector_relations_processor.py`)
- **Action**: After CLIP index: `VectorService.search("clip_image", asset.vectors["clip_image"], limit=10)`. For each result with score ≥ `DAMSettings.vector_relation_threshold`: upsert `Link(source_id=asset.id, target_id=result_id, relation="visually_similar_to", weight=score)`. Skip self. Applies to `["image"]`.
- **Test**: Index 3 similar images. After processing, ≥ 2 `Link` docs with `relation="visually_similar_to"`.
- **Degradation**: < 2 assets in Qdrant → no links created, no exception.

### 7.7 — TaskIQ task + EventBus wiring
- **Action**: Wrap `PipelineOrchestrator.run(asset_id)` as `@broker.task(task_name="dam.run_pipeline")`. In `register_services`: subscribe `dam:asset:ingested` → enqueue task. Register all processors with orchestrator.
- **Test**: Ingest a test image. Wait for task completion (poll `GET /api/dam/pipeline/status`). Assert `asset.status == "ready"`, `ai_caption` non-empty, `vectors.clip_image` length 512.

### Phase 7 Completion
- [ ] **Regression**: Phases 1–6 pass. TaskIQ context propagation intact. Admin module unaffected.
- [ ] **Backlog update**: Mark Phase 7 items + benchmark: CPU time per asset (target < 2 min).
- [ ] **Knowledge capture**: Memory footprint: BLIP ≈1.5 GB, CLIP ≈600 MB, WD14 ≈300 MB — document GPU vs CPU requirement. `@lru_cache` shared between worker processes only if single-process. `applies_to` filter avoids unnecessary model calls for non-image assets.
- [ ] **Self-check**: Upload photo → wait 30 s → `GET /api/dam/assets/{id}` → `status="ready"`, all enrichment fields populated, Qdrant has `clip_image` point.

---

## DAM Phase 8: Search & Discovery
**Maps to**: `dam_design.md §5.6`
**Goal**: Implement `UnifiedSearchService` — three-channel (keyword, vector, graph) hybrid search fused via Reciprocal Rank Fusion, with cursor pagination, faceted counts, and full `AssetFilter` support.

### 8.1 — Search schema models (`schemas/search.py`)
- **Action**: Implement `DateRangeFilter`, `SizeRangeFilter`, `AssetFilter` (with `to_mongo_match() -> Dict`), `SearchRequest`, `AssetSearchHit`, `FacetBucket`, `SearchFacets`, `SearchPage`. Cursor: base64-encoded `(score, id)` tuple.
- **Test**: `AssetFilter(types=["image"]).to_mongo_match()` → `{"asset_types": {"$in": ["image"]}}`. `SearchPage(items=[], total_estimate=0)` valid. Cursor encode/decode round-trip is lossless.

### 8.2 — Keyword search channel
- **Action**: `_keyword_channel(q, filter_match, limit) -> Dict[str, float]`. Use MongoDB `$text:{$search: q}` with `$meta: "textScore"`. Return `{asset_id: rank_position}`.
- **Test**: Insert 3 assets ("cat photo", "dog picture", "cat in garden"). Search `"cat"` → 2 results. Both contain "cat".
- **Degradation**: Text index missing → `OperationFailure` caught, channel returns `{}`, search continues with other channels.

### 8.3 — Vector search channel
- **Action**: `_vector_channel(q, image_bytes, filter_match, limit) -> Dict[str, float]`. Encode query with CLIP. Search `VectorService`. Returns `{}` if `not vector_service._available`.
- **Test**: Ingest + index image. Search with similar text → asset appears in results.
- **Degradation**: Vector service unavailable → `{}` returned, no crash.

### 8.4 — Graph expansion channel
- **Action**: `_graph_channel(seed_ids, depth) -> Dict[str, float]`. MongoDB `$graphLookup` on `Link` collection (walks `visually_similar_to`, `contains` edges). Score = `1 / (1 + hop)`. Bounded by `maxDepth=3`.
- **Test**: Asset A links to B. Keyword channel seeds A. Graph channel adds B. Score(B) < Score(A).
- **Degradation**: Circular links → `maxDepth` prevents infinite traversal.

### 8.5 — RRF fusion, cursor pagination, `search()`
- **Action**: `_rrf_score(rank) = 1 / (60 + rank)`. `search(request: SearchRequest) -> SearchPage`: merge three channel dicts, sort by fused score, apply `AssetFilter`, slice by cursor position, return `SearchPage` with `next_cursor` and `total_estimate = min(10x_limit, actual_count)`.
- **Test**: Two channels each rank different assets; shared asset has highest fused score. Page 1 cursor → page 2 has no duplicates.

### 8.6 — Facets + `find_similar` + reverse image search
- **Action**: `_compute_facets(match)` — parallel MongoDB `$group` aggregations for `asset_types`, `ai_tags`, `detected_objects.class_name`. `find_similar(asset, limit)` — retrieves CLIP vector, Qdrant search; falls back to pHash nearest-neighbor if no vectors. `POST /search/image` — accepts uploaded image, encodes with CLIP, searches.
- **Test**: 5 images + 2 videos → `facets.types["image"].count == 5`, `types["video"].count == 2`.
- **Degradation**: Asset has no vector → pHash fallback returns results without error.

### Phase 8 Completion
- [ ] **Regression**: Phases 1–7 pass. CRUD API (Phase 9) test stubs pass without search.
- [ ] **Backlog update**: Mark Phase 8 items.
- [ ] **Knowledge capture**: RRF k=60 constant rationale (balances precision vs recall). Cursor: encode `json.dumps([score, str(id)])` → base64. `$text` score field name is `textScore` (not `score`). `$graphLookup` `connectFromField`=`target_id`, `connectToField`=`source_id`.
- [ ] **Self-check**: 10 assets. `POST /api/dam/search {"q":"outdoor"}` → results with `matched_by` populated. Cursor loads page 2, no dupes. `GET /api/dam/facets` → correct counts.

---

## DAM Phase 9: API Layer
**Maps to**: `dam_design.md §7`
**Goal**: Wire all REST endpoints into `router.py`. All routes protected by `@require_permission("dam:read")` / `"dam:write"`. OpenAPI docs auto-generated.

### 9.1 — Asset CRUD (`GET/POST/PATCH/DELETE /api/dam/assets`)
- **Action**: `POST /api/dam/assets` (multipart upload → `AssetService.ingest()`), `GET /api/dam/assets` (paginated list, filter by type/status), `GET /api/dam/assets/{id}`, `PATCH /api/dam/assets/{id}` (title, tags, visibility, description), `DELETE /api/dam/assets/{id}` (→ `AssetService.delete()`).
- **Test**: POST → 201 + Asset JSON. PATCH tags → updated doc. DELETE → 204 + doc gone from DB.
- **Degradation**: `GET /api/dam/assets/{nonexistent_id}` → 404 JSON. `DELETE` already-deleted → 404.

### 9.2 — Thumbnail and download endpoints
- **Action**: `GET /api/dam/assets/{id}/thumbnail/{size}` → WebP bytes, `Cache-Control: max-age=86400`. `GET /api/dam/assets/{id}/download` → original file bytes with correct `Content-Disposition`.
- **Test**: Thumbnail → 200 + WebP. Unknown size → 404. Download → `Content-Disposition: attachment; filename="original.jpg"`.

### 9.3 — Search endpoints
- **Action**: `POST /api/dam/search` (JSON body `SearchRequest`), `GET /api/dam/search` (query params → `SearchRequest`), `POST /api/dam/search/image` (multipart image), `GET /api/dam/assets/{id}/similar`, `GET /api/dam/assets/{id}/objects`, `GET /api/dam/facets`.
- **Test**: `POST /search {"q":"cat","limit":5}` → `SearchPage` with `items`, `next_cursor`, `total_estimate`. `GET /search?q=cat&limit=5` → same shape. `GET /facets` → correct type counts.

### 9.4 — Graph and album endpoints
- **Action**: `GET /api/dam/assets/{id}/links?depth=2&direction=out` → adjacency list. Album CRUD: `POST`, `GET`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`, `POST /{id}/assets`, `DELETE /{id}/assets/{assetId}`.
- **Test**: Create album, add 3 assets, assert 3 IDs. Remove 1, assert 2 remain. `GET /links?depth=2` → includes 2nd-hop neighbours.

### 9.5 — Pipeline status and reprocessing endpoints
- **Action**: `GET /api/dam/pipeline/status` → `{total, pending, processing, ready, error, vector_coverage: %}`. `POST /api/dam/assets/{id}/reprocess`. `POST /api/dam/pipeline/reprocess-errors` (bulk, enqueues one task per error asset).
- **Test**: Mark 1 asset as `error` manually. `POST /reprocess-errors` → exactly 1 task enqueued in TaskIQ.

### Phase 9 Completion
- [ ] **Regression**: Phases 1–8 pass. All endpoints in Swagger UI. Admin panel unaffected.
- [ ] **Backlog update**: Mark Phase 9 items.
- [ ] **Knowledge capture**: `Cache-Control: max-age=86400` on thumbnails eliminates redundant thumbnail hits. Multipart upload limit set in FastAPI `UploadFile` — set `MAX_UPLOAD_SIZE_MB` guard in route before passing to service.
- [ ] **Self-check**: All routes visible in `/docs`. Round-trip upload → thumbnail → download via curl.

---

## DAM Phase 10: UI & Integration
**Maps to**: `dam_design.md §8 (UI components) + §10.3–§10.7 (Integration map, pages, hooks)`
**Goal**: Build all NiceGUI UI pages, register DAM in the WebOS shell (launchpad, sidebar, ⌘K palette, header button, admin widget, global asset picker overlay), and integrate with the Blogger module via `PageSlotRegistry`.

### 10.1 — `DAMHooks.register_ui` — full wiring
- **Action**: Register `AppMetadata` for `/dam` (icon `photo_library`, badge_text from settings, keyboard_shortcut `Alt+M`). Add slots: `ui_slots.add("header", dam_quick_upload_button)`, `ui_slots.add("dashboard_widgets", dam_storage_widget)`, `ui_slots.add("asset_picker_overlay", dam_asset_picker_overlay)`. Import all UI page modules to register NiceGUI routes.
- **Test**: `/` launchpad shows DAM card. Header has upload button. Dashboard shows DAM widget.

### 10.2 — Gallery page (`ui/gallery.py`, route `/dam`)
- **Action**: Toolbar (search input, sort dropdown, filter toggle, upload button, grid/list toggle). Filter sidebar (type checkboxes from `/api/dam/facets`, date picker). Asset grid: thumbnail card + filename + type badge + ai_caption + score pill when relevant. Infinite scroll via `next_cursor`. View preference in `app.storage.user["dam_view"]`. Empty-state illustration when no assets.
- **Test**: Navigate to `/dam`. Upload 1 image. Assert gallery card appears. Multi-select 2 assets via Shift+click → bulk action bar appears.
- **Degradation**: Search API 500 → error banner displayed, page does not crash.

### 10.3 — Upload dropzone dialog
- **Action**: `ui.upload()` multi-file dropzone inside `ui.dialog`. Per-file progress bars (poll `GET /api/dam/pipeline/status` by asset ID). Auto-close after all `status="ready"` or show errors inline.
- **Test**: Upload 1 PNG. Progress reaches 100%. Gallery refreshes with new card. Upload 0-byte file → inline validation error, dialog stays open.

### 10.4 — Asset Viewer page (`ui/viewer.py`, route `/dam/assets/{id}`)
- **Action**: Left: full-size preview (image/video/audio/PDF by type) + SVG bbox overlay for `detected_objects`. Right tabbed: General (filename, size, created, hash, status), AI (caption + tag chip cloud + confidence bars), Graph (mini Cytoscape.js from `/api/dam/assets/{id}/links`). Inject `page_slot_registry.render("/dam/assets/{id}", "details_panel")` and `actions_toolbar`.
- **Test**: AI-enriched asset → all 3 tabs populated. Bbox overlay visible on image. Another module injects into `details_panel` slot → extra tab appears.

### 10.5 — Search, Albums, and Graph Explorer pages
- **Action**: `/dam/search` — full-screen query input + image upload toggle + results with `matched_by` pill + live facet sidebar. `/dam/albums` + `/dam/albums/{id}` — album CRUD UI. `/dam/graph` — full-screen Cytoscape.js graph, click node → navigate to viewer, click Expand → fetch 2-hop neighbours.
- **Test**: `/dam/search?q=cat` → results appear. Create album via UI → album card on list page. `/dam/graph` → Cytoscape container renders (JS `cy.nodes().length > 0`).

### 10.6 — Shell components (`ui/components.py`)
- **Action**: `dam_quick_upload_button()` — `upload` icon button in header, tooltip "Upload to Media Library", click opens dropzone dialog. `dam_storage_widget()` — dashboard card with total/ready/processing/error counts from `/api/dam/pipeline/status` + "Open Gallery" link. `dam_asset_picker_overlay()` — single `ui.dialog`, listens for JS `open-asset-picker` custom event, shows mini searchable gallery, fires `asset-selected` on click.
- **Test**: Load `/`. Header has upload icon. Dashboard widget shows counts matching DB state. Fire `open-asset-picker` JS event → picker dialog opens. Click asset → `asset-selected` event fired with correct asset ID.
- **Degradation**: Picker opened while search API is down → empty state + error banner, no unhandled exception.

### 10.7 — Admin widget (`ui/admin_widget.py`) + `DAMHooks.register_admin_widgets`
- **Action**: `DAMAdminWidget` — 2-col-span card: counts row, vector/caption/tag coverage progress bars, action buttons (View Pipeline, Reprocess Errors, Open Gallery). Register via `admin_registry.register_widget(AdminWidget(...))`.
- **Test**: Navigate to `/admin`. DAM widget card present with `photo_library` icon. Counts correct.

### 10.8 — `DAMSettings` full implementation
- **Action**: 20-field settings model from `dam_design.md §10.5` across 5 groups: Gallery, Upload, AI, Search, Watcher. Registered via `register_settings` hookimpl. Immediately editable via `/admin/settings` → DAM tab.
- **Test**: `DAMSettings()` valid with all defaults. `DAMSettings(tagger_threshold=1.5)` → `ValidationError`. `/admin/settings` shows DAM tab with 20 editable fields.

### 10.9 — Blogger cross-module integration
- **Action**: In `src/modules/blogger/hooks.py`: inject `blogger_used_in_posts_tab` builder into `page_slot_registry` for `/dam/assets/{id}` `details_panel` slot. In blog post editor: "Select Cover Image" button fires `open-asset-picker` JS event → on `asset-selected` sets `cover_image_id`.
- **Test**: Blog editor → "Select Image" → asset picker opens. Select asset → `cover_image_id` stored in post form.

### Phase 10 Completion
- [ ] **Regression**: Full suite — all Phases 1–9 pass. All existing modules (Admin, Vault, Blogger, FileCommander) load. `/` launchpad shows DAM card. `/admin/settings` has DAM tab.
- [ ] **Full degradation test**: Kill Qdrant → gallery + upload + text search work; vector search returns empty. Disable AI (`DAM_AI_ENABLED=False`) → all pages load, search via keyword only. Kill MongoDB text index → keyword channel degrades gracefully, vector + graph channels still function.
- [ ] **Backlog update**: Mark all Phase 10 items done. Add final Knowledge Log entry.
- [ ] **Knowledge capture**: Cytoscape.js CDN loading in NiceGUI via `ui.add_head_html`. Shared dialog instance pattern (instantiate once in `dam_asset_picker_overlay`, show/hide on events). `app.storage.user` for per-session view prefs. JS custom event pattern: `open-asset-picker` → NiceGUI Python handler → `asset-selected`. `ui.run_javascript` timing: use `ui.timer(0.1, once=True)` to delay JS calls until DOM is ready.
- [ ] **Self-check**: Login → Launchpad → Media Library → Upload photo → AI enriches → Search "cat" finds it → Click → View AI caption + bbox overlay → Graph Explorer → Blogger editor → Select cover image via picker → Save post.
