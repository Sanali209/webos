from nicegui import ui
from src.ui.layout import layout
from src.core.sdk.data_explorer import DataExplorer
from .models import InventoryItem, OrgNode, ItemCategory
from datetime import datetime, timedelta
import random

class DemoExplorerPage:
    def __init__(self):
        pass

    async def seed_inventory(self):
        """Seed some inventory items if none exist."""
        if await InventoryItem.count() > 0:
            return
        
        categories = list(ItemCategory)
        items = []
        for i in range(20):
            cat = random.choice(categories)
            item = InventoryItem(
                name=f"{cat.value} Item {i+1}",
                category=cat,
                quantity=random.randint(0, 100),
                price=round(random.uniform(10.0, 500.0), 2),
                is_active=random.choice([True, False]),
                last_audit=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            items.append(item)
        
        await InventoryItem.insert_many(items)
        ui.notify("Seeded Inventory Data")

    async def seed_org_chart(self):
        """Seed organization chart if none exist."""
        if await OrgNode.count() > 0:
            return
            
        nodes = [
            OrgNode(name="Acme Corp", role="Root", path="Acme Corp", budget=1000000),
            OrgNode(name="Executive", role="Department", path="Acme Corp/Executive", budget=500000),
            OrgNode(name="Alice CEO", role="CEO", path="Acme Corp/Executive/Alice CEO", budget=200000),
            OrgNode(name="Engineering", role="Department", path="Acme Corp/Engineering", budget=300000),
            OrgNode(name="Bob CTO", role="CTO", path="Acme Corp/Engineering/Bob CTO", budget=150000),
            OrgNode(name="Frontend Team", role="Team", path="Acme Corp/Engineering/Frontend Team", budget=50000),
            OrgNode(name="Charlie Dev", role="Senior Dev", path="Acme Corp/Engineering/Frontend Team/Charlie Dev", budget=0),
            OrgNode(name="Backend Team", role="Team", path="Acme Corp/Engineering/Backend Team", budget=50000),
            OrgNode(name="Dave Dev", role="Junior Dev", path="Acme Corp/Engineering/Backend Team/Dave Dev", budget=0),
            OrgNode(name="Sales", role="Department", path="Acme Corp/Sales", budget=200000),
            OrgNode(name="Eve VP", role="VP Sales", path="Acme Corp/Sales/Eve VP", budget=100000),
        ]
        await OrgNode.insert_many(nodes)
        ui.notify("Seeded Org Chart Data")

    @ui.refreshable
    def render_content(self):
        with ui.column().classes("w-full p-4 gap-4"):
            ui.label("Data Explorer SDK Demo").classes("text-3xl font-bold text-slate-800")
            ui.markdown("""
            This module demonstrates the capabilities of the **DataExplorer SDK**.
            - **Inventory**: Flat list with diverse data types (Enum, Date, Boolean, Number).
            - **Org Chart**: Hierarchical Tree Data visualization using the `path` field.
            """)

            with ui.tabs().classes("w-full") as tabs:
                inv_tab = ui.tab("Inventory")
                org_tab = ui.tab("Organization Chart")
            
            with ui.tab_panels(tabs, value=inv_tab).classes("w-full"):
                with ui.tab_panel(inv_tab):
                    DataExplorer(
                        model=InventoryItem,
                        title="Warehouse Inventory",
                        can_add=True,
                        can_delete=True
                    )
                
                with ui.tab_panel(org_tab):
                    DataExplorer(
                        model=OrgNode,
                        title="Corporate Structure",
                        tree_data=True,
                        path_field="path",
                        path_separator="/",
                        can_add=True,
                        can_delete=True
                    )

    async def render(self):
        # Seed data on first load
        await self.seed_inventory()
        await self.seed_org_chart()

        with layout:
            self.render_content()

@ui.page("/demo-data-explorer")
async def demo_data_explorer_page():
    page = DemoExplorerPage()
    await page.render()
