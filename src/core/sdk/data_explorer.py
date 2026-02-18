from typing import Any, Dict, Iterable, List, Optional, Type, Union
from beanie import Document, PydanticObjectId
from nicegui import ui
from pydantic import BaseModel
from loguru import logger
from datetime import datetime
from enum import Enum

from src.core.middleware import user_id_context
from src.core.models import OwnedDocument

class DataExplorer:
    """
    Auto-GUI SDK component that generates an editable AG Grid from Pydantic or Beanie models.
    """

    def __init__(
        self,
        model: Type[BaseModel],
        items: Optional[Iterable[BaseModel]] = None,
        title: Optional[str] = None,
        on_change: Optional[callable] = None,
        can_add: bool = True,
        can_delete: bool = True,
        auto_save: bool = True,
        tree_data: bool = False,
        path_field: Optional[str] = None,
        path_separator: str = "/"
    ):
        self.model = model
        self.is_beanie = issubclass(model, Document)
        self.title = title or f"{model.__name__} Explorer"
        self.on_change = on_change
        self.can_add = can_add
        self.can_delete = can_delete
        self.auto_save = auto_save
        self.tree_data = tree_data
        self.path_field = path_field
        self.path_separator = path_separator
        self.grid: Optional[ui.aggrid] = None
        
        if self.tree_data and not self.path_field:
            logger.warning("DataExplorer: tree_data is True but path_field is not set.")

        # Internal state for in-memory items
        self._items = list(items) if items is not None else []
        
        self._setup_ui()



    async def _fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch data from the source (Beanie or memory)."""
        raw_data = []
        if self.is_beanie:
            try:
                query = {}
                if issubclass(self.model, OwnedDocument):
                    uid = user_id_context.get()
                    if uid:
                        query = {"owner_id": PydanticObjectId(uid)}
                    else:
                        logger.warning("DataExplorer: No user context for OwnedDocument query.")
                
                documents = await self.model.find(query).to_list()
                raw_data = [doc.model_dump(by_alias=True, mode="json") for doc in documents]
            except Exception as e:
                logger.error(f"DataExplorer: Error fetching Beanie data: {e}")
                ui.notify(f"Database error: {e}", type="negative")
                return []
        else:
            raw_data = [item.model_dump(mode="json") for item in self._items]

        # Post-process for Tree Data (Community Edition Workaround)
        if self.tree_data and self.path_field:
            # 1. Sort by path
            raw_data.sort(key=lambda x: x.get(self.path_field, ""))
            
            # 2. Add level and display name
            for item in raw_data:
                path = item.get(self.path_field, "")
                parts = path.split(self.path_separator)
                item["__level"] = len(parts) - 1
                item["__name"] = parts[-1]
                # We might want to use __name as the display value for the first column?
                # For now, let's keep the original fields but usage of cellRenderer will handle indentation associated with the NAME field.
                
        return raw_data

    def _generate_column_defs(self) -> List[Dict[str, Any]]:
        """Map Pydantic/Beanie fields to AG Grid column definitions."""
        column_defs = []
        
        # Fields to skip (internal or handled separately)
        skip_fields = {"id", "revision_id", "owner_id", "created_at", "updated_at", "created_by", "updated_by"}
        
        # Handle path field visibility
        # In Community simulation, we MIGHT want to hide the full path and show a "Name" column with indentation
        
        is_first_column = True

        for name, field in self.model.model_fields.items():
            if name in skip_fields:
                continue
            
            # Helper to check if this is the "Name" or "Title" field we want to indent
            # Heuristic: If it's the first string field, or explicitly "name"
            
            # Determine title from Field description or name
            header_name = field.description or name.replace("_", " ").title()
            
            col_def = {
                "headerName": header_name,
                "field": name,
                "editable": True,
                "sortable": True,
                "filter": True,
            }
            
            # Type specific logic
            field_type = field.annotation
            
            # Unwrap Optional
            if hasattr(field_type, "__origin__") and field_type.__origin__ is Union:
                args = field_type.__args__
                # Filter out NoneType
                non_none = [a for a in args if a is not type(None)]
                if non_none:
                    field_type = non_none[0]

            if field_type is bool:
                col_def["cellRenderer"] = "agCheckboxCellRenderer"
                col_def["cellEditor"] = "agCheckboxCellEditor"
            elif field_type in (int, float):
                col_def["valueParser"] = "Number(params.newValue)"
            elif field_type is datetime:
                col_def["cellEditor"] = "agDateCellEditor" # Basic date editor
            elif isinstance(field_type, type) and issubclass(field_type, Enum):
                col_def["cellEditor"] = "agSelectCellEditor"
                col_def["cellEditorParams"] = {"values": [e.value for e in field_type]}
            
            # Tree Data Renderer (Community)
            # Apply to the FIRST visible column (usually Name)
            if self.tree_data and is_first_column:
                # Custom renderer to add padding based on __level
                col_def[":cellRenderer"] = """(params) => {
                    const level = params.data.__level || 0;
                    const padding = level * 20;
                    const icon = level > 0 ? '↳ ' : '📁 ';
                    return `<span style="padding-left: ${padding}px; font-weight: ${level === 0 ? 'bold' : 'normal'}">${icon}${params.value}</span>`;
                }"""
                is_first_column = False
            
            column_defs.append(col_def)
            
        # Add a delete column if enabled
        if self.can_delete:
            column_defs.append({
                "headerName": "Actions",
                "field": "id",
                "cellRenderer": "ActionRenderer", # We'll need a custom renderer or just use a button
                "editable": False,
                "width": 100
            })
            
        return column_defs

    def _setup_ui(self):
        """Build the component UI."""
        with ui.column().classes("w-full gap-4"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label(self.title).classes("text-2xl font-bold")
                with ui.row().classes("gap-2"):
                    if self.can_add:
                        ui.button("Add", icon="add", on_click=self._handle_add).props("flat dense")
                    ui.button(icon="refresh", on_click=self.refresh).props("flat dense")
            
            grid_options = {
                "columnDefs": self._generate_column_defs(),
                "rowData": [],
                "stopEditingWhenCellsLoseFocus": True,
                "animateRows": True,
            }

            self.grid = ui.aggrid(grid_options).classes("w-full h-96 shadow-sm")
            
            self.grid.on("cellValueChanged", self._handle_cell_change)
            
            # Initial load
            ui.timer(0, self.refresh, once=True)

    async def refresh(self):
        """Refresh grid data."""
        data = await self._fetch_data()
        self.grid.options["rowData"] = data
        self.grid.update()

    async def _handle_cell_change(self, event):
        """Handle data changes in the grid."""
        row_data = event.args["data"]
        field = event.args["colDef"]["field"]
        new_value = event.args["newValue"]
        
        logger.debug(f"DataExplorer: Change detected in {field}: {new_value}")

        if self.is_beanie:
            try:
                doc_id = row_data.get("_id") or row_data.get("id")
                if not doc_id:
                    logger.error("DataExplorer: No ID found for document update.")
                    return
                
                doc = await self.model.get(PydanticObjectId(doc_id))
                if doc:
                    setattr(doc, field, new_value)
                    await doc.save()
                    ui.notify(f"Updated {field}!")
                else:
                    ui.notify("Document not found.", type="negative")
            except Exception as e:
                logger.error(f"DataExplorer: Error saving Beanie update: {e}")
                ui.notify(f"Update failed: {e}", type="negative")
                await self.refresh() # Revert UI
        else:
            # Update in-memory list
            # Note: This is simplified; in a real app we'd need a more robust way to track which object changed
            index = event.args["rowIndex"]
            if index < len(self._items):
                try:
                    setattr(self._items[index], field, new_value)
                    if self.on_change:
                        self.on_change(self._items)
                    ui.notify(f"Updated {field}!")
                except Exception as e:
                    ui.notify(f"Validation failed: {e}", type="negative")
                    await self.refresh()

    async def _handle_add(self):
        """Placeholder for adding new records. Could open a modal with AutoForm."""
        ui.notify("Addition is not yet implemented in this prototype.", type="info")

    async def _handle_delete(self):
        """Placeholder for deleting records."""
        ui.notify("Deletion is not yet implemented in this prototype.", type="info")
