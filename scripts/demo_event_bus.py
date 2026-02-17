import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.core.event_bus import event_bus, EventEnvelope
from src.core.logging import setup_logging

setup_logging()

async def handle_user_created(envelope: EventEnvelope):
    print(f"📩 [Subscriber] Received event: {envelope.event}")
    print(f"   Payload: {envelope.payload}")
    print(f"   Context: {envelope.context}")
    print(f"   Timestamp: {envelope.timestamp}")

async def main():
    print("🚀 Starting Event Bus Demo...")
    
    # 1. Subscribe
    event_bus.subscribe("user:created", handle_user_created)
    print("✅ Subscribed to 'user:created'")

    # 2. Emit
    print("📢 Emitting 'user:created' event...")
    payload = {"username": "jdoe", "email": "jdoe@example.com"}
    context = {"trace_id": "12345", "user_id": "admin-1"}
    
    await event_bus.emit("user:created", payload, context)
    
    # Allow some time for async handlers
    await asyncio.sleep(0.1)
    print("🏁 Demo Complete")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
