import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.modules.dam.services.watcher_service import WatcherService
from src.modules.dam.services.asset_service import AssetService

@pytest.fixture
def mock_asset_service():
    return MagicMock(spec=AssetService)

@pytest.mark.asyncio
async def test_watcher_service_reload_watches(mock_asset_service):
    # Initialize WatcherService
    watcher = WatcherService(asset_service=mock_asset_service, system_owner_id="system")
    
    # Paths to watch
    path1 = Path("/tmp/watch_dir_1")
    path2 = Path("/tmp/watch_dir_2")
    path3 = Path("/tmp/watch_dir_3")
    
    # First, let's start the watcher with two paths
    watcher.add_watch(path1)
    watcher.add_watch(path2)
    
    assert len(watcher.watched_paths) == 2
    assert watcher._running is False
    
    # We won't actually start the real watchdog thread to avoid blocking tests,
    # but we can call reload_watches and ensure state updates correctly.
    
    # Mock stop and start to prevent actual thread spawning during unit testing
    with patch.object(watcher, 'start') as mock_start, \
         patch.object(watcher, 'stop') as mock_stop:
        
        await watcher.reload_watches([path3])
        
        # Ensure stop was called to clean up old observer
        mock_stop.assert_called_once()
        
        # Ensure the paths were cleared and the new one was added
        assert len(watcher.watched_paths) == 1
        assert watcher.watched_paths[0] == path3
        
        # Ensure start was called to spin up the new observer
        mock_start.assert_called_once()

@pytest.mark.asyncio
async def test_watcher_service_add_watch(mock_asset_service):
    watcher = WatcherService(asset_service=mock_asset_service, system_owner_id="system")
    path = Path("/tmp/watch_dir_test")
    watcher.add_watch(path)
    
    assert len(watcher.watched_paths) == 1
    assert watcher.watched_paths[0] == path
