import asyncio
import pytest
from src.core.event_bus import event_bus, EventEnvelope

class TestEventBus:
    @pytest.mark.asyncio
    async def test_subscribe_and_emit(self):
        received = []

        async def handler(envelope: EventEnvelope):
            received.append(envelope)

        event_bus.subscribe("test:event", handler)
        await event_bus.emit("test:event", {"data": "foo"})

        # Allow loop to process
        await asyncio.sleep(0.01)

        assert len(received) == 1
        assert received[0].payload == {"data": "foo"}
        assert received[0].event == "test:event"

    @pytest.mark.asyncio
    async def test_exception_suppression(self):
        # Ensure one failing handler doesn't crash the bus
        async def failing_handler(envelope):
            raise ValueError("Boom")

        received = []
        async def success_handler(envelope):
            received.append(envelope)

        event_bus.subscribe("test:error", failing_handler)
        event_bus.subscribe("test:error", success_handler)

        await event_bus.emit("test:error", {})
        await asyncio.sleep(0.01)

        assert len(received) == 1
