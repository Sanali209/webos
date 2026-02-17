import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from loguru import logger


@dataclass
class EventEnvelope:
    event: str
    payload: Any
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event: str, handler: Callable) -> None:
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(handler)
        logger.debug(f"Subscribed to event: {event}")

    async def emit(self, event: str, payload: Any, context: Optional[Dict] = None) -> None:
        if event not in self._subscribers:
            return

        envelope = EventEnvelope(event=event, payload=payload, context=context or {})
        
        # Create tasks for all handlers to run concurrently
        tasks = []
        for handler in self._subscribers[event]:
            tasks.append(self._invoke_handler(handler, envelope))
        
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _invoke_handler(self, handler: Callable, envelope: EventEnvelope) -> None:
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(envelope)
            else:
                handler(envelope)
        except Exception as e:
            logger.error(f"Error handling event {envelope.event}: {e}")
            # We suppress the exception to not crash the publisher

event_bus = EventBus()
