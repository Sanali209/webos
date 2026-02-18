# Core Concepts: The Event Bus

This tutorial will teach you how to use the WebOS Event Bus to create decoupled, reactive communication between modules.

## Learning Objectives
- Subscribing to system events.
- Emitting custom events.
- Handling event payloads safely.

## 1. What is the Event Bus?
The Event Bus is an asynchronous message broker that lives inside the WebOS Kernel. It allows modules to "shout" about things that happened (Emitting) and other modules to "listen" for those things (Subscribing), without knowing anything about each other.

## 2. Listening for Events
To listen for an event, use the `@bus.on` decorator.

### Example: Log when a user logs in
In your module's `hooks.py` or `router.py`:

```python
from src.core.event_bus import bus
from loguru import logger

@bus.on("auth:login:success")
async def on_user_login(payload):
    user_email = payload.get("email")
    logger.info(f"AUDIT: User {user_email} has entered the system.")
```

## 3. Emitting Events
To trigger an event, use `await bus.emit(event_name, payload)`.

### Example: Notify when a blog post is published
In `src/modules/blogger/ui.py`:

```python
from src.core.event_bus import bus

async def publish_post(post):
    # Save to DB...
    await post.insert()
    
    # Notify the rest of the system
    await bus.emit("blogger:post:published", {
        "title": post.title,
        "slug": post.slug,
        "author": post.owner_id
    })
```

## 4. Why Use the Event Bus?
Imagine you want to send a Slack notification whenever a blog post is published. 
- **Without the Bus**: You'd have to import a `SlackService` directly into the `Blogger` module and call it inside the `publish_post` function. Now `Blogger` depends on `Slack`.
- **With the Bus**: `Blogger` just emits `blogger:post:published`. You can create a completely separate `Notification` module that listens for that event and sends the Slack message. `Blogger` doesn't even know Slack exists!

## 🧪 Try it Yourself
1. Create a new module folder `src/modules/listener_demo`.
2. Add an `__init__.py`.
3. Add a `router.py` with the following:
```python
from fastapi import APIRouter
from src.core.event_bus import bus

router = APIRouter()

@bus.on("auth:login:success")
async def welcome_shout(payload):
    print(f"HELLO WORLD! {payload.get('email')} just logged in!")
```
4. Restart the server and log in. Watch your terminal for the print message!

---

## Next Steps
- Learn how to [Protect a Route](../howto/protect_route.md).
- Understand the [Module Auto-Discovery](../concepts/module_system.md).
