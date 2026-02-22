# How-To: Emit and Subscribe to Events

WebOS modules should remain decoupled. Instead of Module A importing Module B directly to run a function, Module A emits an event, and Module B listens for it. This is handled by the `EventBus`.

## Subscribing to an Event

Use `event_bus.subscribe` to register a handler for a specific event topic. The handler recieves an `EventEnvelope` containing the event name, payload, and generating context.

```python
import asyncio
from src.core.event_bus import event_bus, EventEnvelope
from loguru import logger

async def on_user_created(envelope: EventEnvelope):
    user_data = envelope.payload
    logger.info(f"Received user creation event for {user_data['email']}")
    logger.debug(f"Event occurred at: {envelope.timestamp}")

    # Perform background tasks, e.g., send welcome email
    await send_welcome_email(user_data['email'])

# Typically called during module initialization (e.g., in a startup hook)
event_bus.subscribe("user:created", on_user_created)
```

## Emitting an Event

To trigger the handlers, use `event_bus.emit`. This is an asynchronous operation. Handlers are executed concurrently using `asyncio.gather`, and any exceptions in handlers are caught and logged so they do not crash the publisher.

```python
from src.core.event_bus import event_bus

async def create_new_user(email: str, name: str):
    # 1. Business logic to save user to DB
    user = {"email": email, "name": name, "id": 123}
    
    # 2. Emit the event with a payload dictionary
    await event_bus.emit(
        event="user:created", 
        payload=user,
        # Optional: Pass context like the user triggered the action
        context={"initiated_by": "admin_uuid"} 
    )
    
    return user
```

### Event Topics Pattern
We standardize on the `entity:action` topic naming convention:
- `user:created`
- `invoice:paid`
- `asset:deleted`
