# Engine Bootstrapping User Manual

This manual explains how to initialize and start the Web OS Engine in your application.

## 1. Minimal Engine Setup
To start the engine with the default configuration, follow these steps:

```python
import asyncio
from src.core.kernel import Engine

async def main():
    engine = Engine()
    
    # 1. Discover modules in src.modules
    engine.discover_modules()
    
    # 2. Boot the engine
    await engine.start()
    
    # Keep the engine running if needed
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## 2. Directory Structure
The engine expects modules to be located in the `src/modules` package. Each sub-directory with an `__init__.py` and a class inheriting from `IModule` will be automatically discovered.

## 3. Safe Shutdown
Always call `await engine.stop()` to ensure that all modules have a chance to clean up resources (database connections, open files, etc.) via their `shutdown()` method.
