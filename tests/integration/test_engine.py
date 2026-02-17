import pytest
from src.core.kernel import Engine
from src.core.di import DIContainer
from src.modules.demo.module import DemoModule

@pytest.mark.asyncio
async def test_engine_boot_and_discovery():
    # Use a fresh container for testing
    test_di = DIContainer()
    engine = Engine(di_container=test_di)
    
    # Discovery (should find src.modules.demo)
    engine.discover_modules()
    
    assert "demo" in engine._modules
    demo_mod = engine._modules["demo"]
    assert isinstance(demo_mod, DemoModule)
    
    # Start (Boot Sequence)
    await engine.start()
    assert demo_mod.initialized is True
    
    # Stop (Shutdown Sequence)
    await engine.stop()
    assert demo_mod.shutdown_done is True

@pytest.mark.asyncio
async def test_hook_execution():
    from src.core.hooks import hookimpl
    test_di = DIContainer()
    engine = Engine(di_container=test_di)
    
    # Track hook calls
    hook_calls = []

    class MockPlugin:
        @hookimpl
        async def post_setup(self):
            hook_calls.append("post_setup")
        
        @hookimpl
        def mount_ui(self):
            hook_calls.append("mount_ui")

    engine.pm.register(MockPlugin())
    
    await engine.start()
    assert "post_setup" in hook_calls
    assert "mount_ui" in hook_calls
