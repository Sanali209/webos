import pytest
from unittest.mock import AsyncMock, patch
from src.ui.components.folder_picker import FolderPicker

# Since nicegui tests typically require a browser or specific testing harnesses,
# we construct the component and mock the storage_manager to test its methods directly.

@pytest.fixture
def mock_storage_manager():
    with patch('src.ui.components.folder_picker.storage_manager') as mock:
        mock.list_dir = AsyncMock()
        yield mock

def test_folder_picker_init(mock_storage_manager):
    callback = lambda x: print(x)
    picker = FolderPicker(callback=callback, base_path="fs://local/folder")
    
    assert picker.current_path == "fs://local/folder"
    assert picker.callback == callback

def test_folder_picker_navigate_up(mock_storage_manager):
    callback = lambda x: print(x)
    picker = FolderPicker(callback=callback, base_path="fs://local/folder/subfolder/")
    
    # Mock asyncio create_task to prevent actually running the refresh loop
    with patch('asyncio.create_task'):
        picker.navigate_up()
        
    assert picker.current_path == "fs://local/folder/"
    
    # Test navigating up to root
    with patch('asyncio.create_task'):
        picker.navigate_up()
        picker.navigate_up()
        
    assert picker.current_path == "fs://local/"

def test_folder_picker_navigate_down(mock_storage_manager):
    callback = lambda x: print(x)
    picker = FolderPicker(callback=callback, base_path="fs://local/folder/")
    
    # Mock asyncio create_task
    with patch('asyncio.create_task'):
        picker.navigate_down("subfolder")
        
    assert picker.current_path == "fs://local/folder/subfolder/"
