from typing import List, Type, Any
from beanie import Document
from loguru import logger
from src.core.hooks import hookimpl
from src.core.module_loader import loader

from src.core.registry import ServiceRegistry
from src.modules.dam.models import Asset, Link, Album
from src.modules.dam.services.builtin_types import (
    ImageAssetType, VideoAssetType, AudioAssetType, DocumentAssetType, UrlAssetType
)
from src.modules.dam.services.type_registry import asset_type_registry

from src.core.services.settings_service import settings_service
from src.modules.dam.settings import DAMSettings
from src.modules.dam.services.asset_service import AssetService
from src.modules.dam.services.thumbnail_service import ThumbnailGenerator
from src.modules.dam.services.watcher_service import WatcherService
from src.core.event_bus import event_bus
import asyncio
from pathlib import Path
from beanie.odm.fields import PydanticObjectId

from src.modules.dam.services.vector_service import VectorService
from src.modules.dam.services.unified_search import UnifiedSearchService
from src.modules.dam.drivers.manager import AssetDriverManager
from src.modules.dam.drivers.image_driver import ImageDriver
from src.modules.dam.drivers.video_driver import VideoDriver
from src.modules.dam.drivers.audio_driver import AudioDriver
from src.modules.dam.drivers.document_driver import DocumentDriver

from src.core.config import settings

class DAMHooks:
    module_name = "dam"

    @hookimpl
    def register_models(self) -> List[Type[Document]]:
        return [Asset, Link, Album]
        
    @hookimpl
    def register_routes(self, app: Any) -> None:
        from src.modules.dam.router import router
        app.include_router(router)
        
    @hookimpl
    def register_asset_types(self) -> List[Any]:
        return [
            ImageAssetType(),
            VideoAssetType(),
            AudioAssetType(),
            DocumentAssetType(),
            UrlAssetType()
        ]

    @hookimpl
    def register_asset_drivers(self) -> List[Any]:
        return [
            ImageDriver(),
            VideoDriver(),
            AudioDriver(),
            DocumentDriver()
        ]
        
    @hookimpl
    def register_settings(self) -> type:
        return DAMSettings

    @hookimpl
    def register_services(self) -> None:
        """
        Initialize the Driver manager and core DAM services.
        """
        # Load typed settings securely
        dam_settings = settings_service.get_typed("dam", DAMSettings)
        
        # 1. Asset Service
        asset_svc = AssetService()
        ServiceRegistry.register(AssetService, asset_svc)
        
        # 2. Thumbnail Generator
        thumb_gen = ThumbnailGenerator(
            cache_dir=dam_settings.cache_dir,
            sizes=dam_settings.thumbnail_sizes
        )
        ServiceRegistry.register(ThumbnailGenerator, thumb_gen)
        
        # 3. Watcher Service 
        watcher = WatcherService(
            asset_service=asset_svc,
            system_owner_id=dam_settings.system_owner_id
        )
        # Bind monitored filesystem paths inherently overriding constraints conditionally
        for p in dam_settings.watch_paths:
            watcher.add_watch(Path(p))
            
        ServiceRegistry.register(WatcherService, watcher)
        
        # 4. Driver Manager
        manager = AssetDriverManager()
        drivers = loader.get_all_asset_drivers()
        for driver in drivers:
            manager.register(driver)
            
        ServiceRegistry.register(AssetDriverManager, manager)
        logger.info(f"DAM: Registered AssetDriverManager containing {len(drivers)} drivers.")

        # 5. Vector Service
        vector_svc = VectorService(url=settings.QDRANT_URL)
        ServiceRegistry.register(VectorService, vector_svc)

        # 6. Unified Search Service
        ServiceRegistry.register(UnifiedSearchService, UnifiedSearchService())

        # 7. Pipeline Orchestrator
        from src.modules.dam.services.pipeline_orchestrator import PipelineOrchestrator
        from src.modules.dam.processors.clip_processor import CLIPProcessor
        from src.modules.dam.processors.blip_processor import BLIPProcessor
        from src.modules.dam.processors.tag_processor import TagProcessor
        from src.modules.dam.processors.detection_processor import DetectionProcessor
        from src.modules.dam.processors.structural_processor import StructuralProcessor
        from src.modules.dam.processors.relation_processor import VectorRelationProcessor

        orchestrator = PipelineOrchestrator([
            CLIPProcessor(),
            BLIPProcessor(),
            TagProcessor(),
            DetectionProcessor(),
            StructuralProcessor(),
            VectorRelationProcessor() # Must be last
        ])
        ServiceRegistry.register(PipelineOrchestrator, orchestrator)
        logger.info(f"DAM: Registered PipelineOrchestrator with {len(orchestrator.processors)} processors.")

        # ==============================================================
        # Internal Event Bus Bindings bridging bounded context execution
        # ==============================================================
        async def on_asset_ingested(envelope):
            asset_id = envelope.payload
            from src.modules.dam.models import Asset
            from src.modules.dam.tasks import run_ai_pipeline
            
            asset = await Asset.get(asset_id)
            if not asset: return
                
            # 1. Sync Processors (Metadata & Thumbnails)
            await thumb_gen.generate(asset)
            await manager.process(asset)
            
            # 2. Async AI Pipeline (TaskIQ)
            await run_ai_pipeline.kiq(str(asset_id))
            
        event_bus.subscribe("dam:asset:ingested", on_asset_ingested)

    @hookimpl
    async def on_startup_async(self) -> None:
        """
        Delayed bounds execution triggering Watchdog routines independently off FastAPI block.
        """
        # Ensure imports mapping 
        from src.modules.dam.tasks import dam_scavenger_task
        
        try:
            watcher = ServiceRegistry.get(WatcherService)
            await watcher.start()
        except ValueError:
            logger.warning("DAM: WatcherService was not registered successfully.")

        try:
            vector_svc = ServiceRegistry.get(VectorService)
            await vector_svc.ensure_collections()
        except Exception as e:
            logger.error(f"DAM: Failed to initialize VectorService collections: {e}")
        
        types = loader.get_all_asset_types()
        for t in types:
            asset_type_registry.register(t)
        logger.info(f"DAM: Registered {len(types)} asset types from modules.")

    @hookimpl
    def register_ui(self):
        """Register the Media Library app and its nicegui routes."""
        logger.info("=========== DAMHOOKS REGISTER_UI IS EXECUTING! ==============")
        import sys
        print("=========== DAMHOOKS REGISTER_UI IS EXECUTING! (sys.stdout) ==============", flush=True)
        from src.ui.registry import ui_registry, AppMetadata
        from src.modules.dam.ui import gallery, components, viewer, search, albums, graph_explorer
        
        ui_registry.register_app(AppMetadata(
            name="Media Library",
            icon="photo_library",
            route="/dam",
            description="Intelligent Digital Asset Management",
            category="Core"
        ))
        
        ui_registry.register_app(AppMetadata(
            name="Albums",
            icon="collections",
            route="/dam/albums",
            description="Browse curated asset collections",
            category="Core"
        ))
        
        ui_registry.register_app(AppMetadata(
            name="Reverse Search",
            icon="image_search",
            route="/dam/search",
            description="Visual similarity and semantic search",
            category="Core"
        ))
        
        ui_registry.register_app(AppMetadata(
            name="Visual Explorer",
            icon="hub",
            route="/dam/graph",
            description="Navigate the DAM knowledge graph",
            category="Core"
        ))
        
        # We can configure global slots here, or they can configure themselves in their module space
        components.register_global_slots()

    @hookimpl
    def register_page_slots(self):
        from src.ui.page_slot_registry import PageSlotRegistry
        pass  # We could declare dam slots here directly, but PageSlotRegistry handles dynamic injection better, skipping for now, relying on viewer.py to declare

    @hookimpl
    def register_admin_widgets(self):
        """Register DAM-specific widgets on the admin dashboard."""
        from src.modules.dam.ui.admin_widget import DAMAdminWidget
        from src.ui.admin_registry import admin_registry

        admin_registry.register_widget(DAMAdminWidget())

# Export an instance of the hooks for the module loader to discover
hooks = DAMHooks()
