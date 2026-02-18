import asyncio
import random
from src.core.tasks import broker
from loguru import logger

@broker.task
async def generate_report_task(report_name: str):
    """
    Simulates a long-running report generation.
    Updates progress via TaskIQ result metadata or separate event if needed.
    """
    logger.info(f"Starting report generation: {report_name}")
    
    total_steps = 10
    for i in range(1, total_steps + 1):
        await asyncio.sleep( random.uniform(0.5, 1.5) )
        progress = (i / total_steps) * 100
        logger.debug(f"Report '{report_name}' progress: {progress}%")
        # In a real app, we might emit an event or update a DB field here.
        # TaskIQ results can also store partial state if configured.
    
    logger.success(f"Report generation complete: {report_name}")
    return {"status": "success", "report_url": f"/files/reports/{report_name}.pdf"}
