# Phase 3: Module System & Auto-Discovery Implementation Plan

This phase implements a "Convention over Configuration" module system using `Pluggy` and dynamic imports.

## Proposed Changes

### Core Hooks & Discovery
#### [NEW] [hooks.py](file:///d:/github/webos/src/core/hooks.py)
- Define `pluggy` markers.
- Define `WebOSHookSpec` for lifecycle and extension hooks.

#### [NEW] [module_loader.py](file:///d:/github/webos/src/core/module_loader.py)
- Implement `ModuleLoader` to scan `src/modules`.
- Support auto-discovery of `models.py`, `router.py`, and `hooks.py`.
- Maintain a registry of loaded modules.

### Application Integration
#### [MODIFY] [main.py](file:///d:/github/webos/src/main.py)
- Use `ModuleLoader` to discover plugins.
- Collect all models for Beanie initialization.
- Register all discovered routers.
- Trigger lifecycle hooks.

### Demonstration Module
#### [NEW] [demo_hello_world](file:///d:/github/webos/src/modules/demo_hello_world/)
- Implement a minimal module to prove auto-discovery works.

## Verification Plan

### Automated Tests
- **Module Discovery**: Test that `ModuleLoader` identifies modules correctly.
    - Command: `python -m pytest tests/core/test_module_loader.py`
- **Hook Execution**: Test that `pluggy` hooks are called.

### Manual Verification
- Start the server: `.venv/Scripts/python -m uvicorn src.main:app --port 8000`
- Inspect `http://localhost:8000/docs` to see if `demo_hello_world` endpoints are registered.
- Check logs for "Module demo_hello_world loaded" messages.
