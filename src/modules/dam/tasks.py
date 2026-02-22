from loguru import logger
from pathlib import Path
from src.core.tasks import broker
from src.core.registry import ServiceRegistry
from src.modules.dam.services.watcher_service import WatcherService
from src.modules.dam.services.asset_service import AssetService
from src.modules.dam.models import Asset, AssetStatus
from beanie import PydanticObjectId

@broker.task(schedule=[{"cron": "*/15 * * * *"}])
async def dam_scavenger_task():
    """
    Periodic job (via taskiq cron) bridging system gaps caused by server downtime 
    by scraping watched directories correcting structural drift securely.
    """
    watcher_service = ServiceRegistry.get_optional(WatcherService)
    asset_service = ServiceRegistry.get_optional(AssetService)

    if not watcher_service or not asset_service:
        return

    logger.info("DAM Scavenger Task: commencing file-system audit drift sync...")

    # Phase 1: Discover new untracked items mapping into standard Index
    system_owner_id = watcher_service._system_owner_id
    tracked_urns = set()
    
    for watch_path in watcher_service.watched_paths:
        for file_path in watch_path.rglob("*"):
            if not file_path.is_file(): continue
            # Exclude known ignores manually matching patterns 
            if any(file_path.name.endswith(ext.replace("*", "")) for ext in [".tmp", ".part", ".DS_Store"]): 
                continue

            fs_urn = f"fs://local/{file_path.as_posix()}"
            tracked_urns.add(fs_urn)
            
            existing = await Asset.find_one(Asset.storage_urn == fs_urn)
            if not existing:
                await asset_service.register_path(file_path, owner_id=system_owner_id)

    # Phase 2: Verify existing physical states
    async for asset in Asset.find(Asset.status != AssetStatus.MISSING):
        # We only care about local managed boundaries not strictly URL virtual entities 
        if not asset.storage_urn.startswith("fs://local/"): 
            continue
            
        local_path = Path(asset.storage_urn.replace("fs://local/", ""))
        if not local_path.exists():
            asset.status = AssetStatus.MISSING
            await asset.save()
            logger.warning(f"DAM Scavenger: Asset {asset.id} marked MISSING: {local_path}")

    # Phase 3: Re-discover resurrected previously offline elements
    async for asset in Asset.find(Asset.status == AssetStatus.MISSING):
        if not asset.storage_urn.startswith("fs://local/"): 
            continue
            
        local_path = Path(asset.storage_urn.replace("fs://local/", ""))
        if local_path.exists():
            await asset_service.refresh_asset(local_path)
            logger.info(f"DAM Scavenger: Recovered Asset {asset.id} successfully.")

    logger.info("DAM Scavenger Task: completed audit run.")

@broker.task(task_name="dam.run_ai_pipeline")
async def run_ai_pipeline(asset_id: str):
    """
    Background job executing the AI enrichment pipeline.
    """
    from src.modules.dam.services.pipeline_orchestrator import PipelineOrchestrator
    
    orchestrator = ServiceRegistry.get_optional(PipelineOrchestrator)
    if not orchestrator:
        logger.error("run_ai_pipeline: PipelineOrchestrator not registered.")
        return
        
    await orchestrator.run(PydanticObjectId(asset_id))

