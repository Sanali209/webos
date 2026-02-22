from typing import List
from loguru import logger
from beanie import PydanticObjectId

from src.modules.dam.models import Asset, AssetStatus
from src.modules.dam.processors.base import BasePipelineProcessor

class PipelineOrchestrator:
    """
    Orchestrates the AI enrichment pipeline for assets.
    """
    
    def __init__(self, processors: List[BasePipelineProcessor] = None):
        self.processors = processors or []

    def register_processor(self, processor: BasePipelineProcessor):
        self.processors.append(processor)
        logger.debug(f"PipelineOrchestrator: Registered processor '{processor.name}'")

    async def run(self, asset_id: PydanticObjectId):
        """
        Runs the pipeline for a single asset.
        """
        asset = await Asset.get(asset_id)
        if not asset:
            logger.error(f"PipelineOrchestrator: Asset {asset_id} not found.")
            return

        logger.info(f"PipelineOrchestrator: Starting pipeline for {asset.filename} ({asset_id})")
        
        asset.status = AssetStatus.PROCESSING
        # Initialize error tracking if not present
        if "pipeline_errors" not in asset.metadata:
            asset.metadata["pipeline_errors"] = {}
        await asset.save()

        has_errors = False
        processed_count = 0

        for processor in self.processors:
            if asset.primary_type in processor.applies_to:
                try:
                    logger.debug(f"PipelineOrchestrator: Executing {processor.name} for {asset_id}")
                    await processor.process(asset)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"PipelineOrchestrator: {processor.name} failed for {asset_id}: {e}")
                    asset.metadata["pipeline_errors"][processor.name] = str(e)
                    has_errors = True
            else:
                logger.trace(f"PipelineOrchestrator: Skipping {processor.name} for type {asset.primary_type}")

        # Update final status
        if has_errors:
            asset.status = AssetStatus.PARTIAL
        else:
            asset.status = AssetStatus.READY
            
        await asset.save()
        logger.info(f"PipelineOrchestrator: Completed pipeline for {asset_id}. Processors ran: {processed_count}. Status: {asset.status}")
