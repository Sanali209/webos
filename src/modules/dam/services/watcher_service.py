import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler, FileCreatedEvent,
    FileMovedEvent, FileDeletedEvent, FileModifiedEvent,
    PatternMatchingEventHandler,
)
from loguru import logger
from beanie import PydanticObjectId
from src.modules.dam.services.asset_service import AssetService

IGNORED_PATTERNS = ["*.tmp", "*.part", ".DS_Store", "Thumbs.db", "~*"]
WATCHED_EXTENSIONS = ["*.jpg", "*.jpeg", "*.png", "*.tiff", "*.webp",
                       "*.mp4", "*.mov", "*.pdf", "*.mp3", "*.wav", "*.md", "*.txt"]

class DAMEventHandler(PatternMatchingEventHandler):
    """
    Watchdog handler. Puts events on an asyncio.Queue, never calls I/O directly.
    """
    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        super().__init__(
            patterns=WATCHED_EXTENSIONS,
            ignore_patterns=IGNORED_PATTERNS,
            ignore_directories=True,
            case_sensitive=False,
        )
        self._queue = queue
        self._loop = loop

    def _put(self, event_type: str, **kwargs):
        self._loop.call_soon_threadsafe(
            self._queue.put_nowait, {"type": event_type, **kwargs}
        )

    def on_created(self, event):
        self._put("created", path=event.src_path)

    def on_deleted(self, event):
        self._put("deleted", path=event.src_path)

    def on_moved(self, event):
        self._put("moved", src=event.src_path, dst=event.dest_path)

    def on_modified(self, event):
        self._put("modified", path=event.src_path)

class WatcherService:
    """
    Lifecycle managed by `on_startup_async` pluggy integration.
    Manages configured paths checking external modifications consistently debouncing noise.
    """
    DEBOUNCE_SECONDS = 2.0

    def __init__(self, asset_service: AssetService, system_owner_id: str):
        self._asset_service = asset_service
        self._system_owner_id = PydanticObjectId(system_owner_id) if system_owner_id != "system" else PydanticObjectId()
        self._queue: asyncio.Queue = asyncio.Queue()
        self._observer = Observer()
        self._pending: dict[str, asyncio.TimerHandle] = {}
        self.watched_paths: list[Path] = []
        self._running = False

    def add_watch(self, path: Path, recursive: bool = True):
        """Bind physical directory constraints."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            handler = DAMEventHandler(self._queue, asyncio.get_event_loop())
            self._observer.schedule(handler, str(path), recursive=recursive)
            self.watched_paths.append(path)
            logger.info(f"WatcherService: watching {path} (recursive={recursive})")
        except Exception as e:
            logger.warning(f"WatcherService failed binding mapping against {path}: {e}")

    async def start(self):
        """Bootstraps isolated observer threads effectively freeing WebOS event handling natively."""
        if not self.watched_paths:
            logger.info("WatcherService: Watch paths configuration empty. Skipping.")
            return

        self._observer.start()
        self._running = True
        asyncio.create_task(self._fsync_worker())
        logger.info("WatcherService started successfully.")

    async def stop(self):
        """Shut down observer lifecycle preventing thread leakages globally."""
        if self._running:
            self._running = False
            self._observer.stop()
            await asyncio.to_thread(self._observer.join)

    async def _fsync_worker(self):
        """Consumes events from queue with debouncing."""
        loop = asyncio.get_running_loop()
        while self._running:
            try:
                # Add tiny timeout checking bound state updates seamlessly
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            key = event.get("path") or event.get("src")

            # Reset bounce timing map
            if key in self._pending:
                self._pending[key].cancel()

            handle = loop.call_later(
                self.DEBOUNCE_SECONDS,
                lambda e=event: asyncio.create_task(self._dispatch(e))
            )
            self._pending[key] = handle

    async def _dispatch(self, event: dict):
        """Routes delayed mapped queue items sequentially parsing standard AssetServices calls."""
        try:
            match event["type"]:
                case "created":
                    await self._asset_service.register_path(Path(event["path"]), self._system_owner_id)
                case "modified":
                    logger.debug(f"Handling modified: {event['path']}")
                    # Re-hash internal references without recreating UUID
                    await self._asset_service.refresh_asset(Path(event["path"]))
                case "moved":
                    logger.debug(f"Handling moved: {event['src']} -> {event['dst']}")
                    await self._asset_service.update_storage_urn(Path(event["src"]), Path(event["dst"]))
                case "deleted":
                    logger.debug(f"Handling deleted: {event['path']}")
                    await self._asset_service.mark_missing(Path(event["path"]))
        except Exception as e:
            logger.error(f"WatcherService dispatch mapped tracking error resolving state {event}: {e}")
