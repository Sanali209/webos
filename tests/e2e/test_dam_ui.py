"""
E2E Tests for WebOS using Playwright.

REQUIREMENTS: Start the WebOS server before running:
    python run.py

Then run the tests:
    pytest tests/e2e/ -v --browser chromium --base-url=http://127.0.0.1:8000
"""

import pytest
from playwright.sync_api import Page, expect


# Helper: navigate and wait for NiceGUI's Vue.js to finish rendering
def go(page: Page, url: str, timeout: int = 15000):
    page.goto(url)
    page.wait_for_load_state("networkidle", timeout=timeout)


# =============================================================================
# LAUNCHPAD & SIDEBAR TESTS
# =============================================================================

class TestLaunchpad:
    """Tests that the home page Launchpad renders all expected apps."""

    def test_launchpad_loads(self, page: Page, base_url: str):
        """The home page loads and renders the 'LAUNCHPAD' section header."""
        go(page, base_url)
        expect(page.get_by_text("LAUNCHPAD").first).to_be_visible(timeout=10000)

    def test_launchpad_has_media_library(self, page: Page, base_url: str):
        """Media Library app card appears on the Launchpad."""
        go(page, base_url)
        # Multiple matches expected (sidebar + card title) — just verify at least one
        assert page.get_by_text("Media Library", exact=True).count() >= 1

    def test_launchpad_has_albums(self, page: Page, base_url: str):
        """Albums app card appears on the Launchpad."""
        go(page, base_url)
        assert page.get_by_text("Albums", exact=True).count() >= 1

    def test_launchpad_has_reverse_search(self, page: Page, base_url: str):
        """Reverse Search app card appears on the Launchpad."""
        go(page, base_url)
        assert page.get_by_text("Reverse Search", exact=True).count() >= 1

    def test_launchpad_has_visual_explorer(self, page: Page, base_url: str):
        """Visual Explorer app card appears on the Launchpad."""
        go(page, base_url)
        assert page.get_by_text("Visual Explorer", exact=True).count() >= 1

    def test_launchpad_click_navigates_to_dam(self, page: Page, base_url: str):
        """Clicking Media Library card navigates to /dam."""
        go(page, base_url)
        # Click the launchpad card specifically (description text is unique)
        page.get_by_text("Intelligent Digital Asset Management").click()
        page.wait_for_url("**/dam**", timeout=8000)
        assert "/dam" in page.url


class TestSidebar:
    """Tests that the sidebar Navigator contains the correct navigation links."""

    def test_sidebar_has_media_library(self, page: Page, base_url: str):
        """Media Library link appears in the sidebar."""
        go(page, base_url)
        assert page.get_by_text("Media Library").count() >= 1

    def test_sidebar_has_albums(self, page: Page, base_url: str):
        """Albums link appears in the sidebar."""
        go(page, base_url)
        assert page.get_by_text("Albums").count() >= 1


# =============================================================================
# DAM PAGE TESTS
# =============================================================================

class TestDAMGallery:
    """Tests for the main DAM gallery at /dam."""

    def test_gallery_page_loads(self, page: Page, base_url: str):
        """The /dam page returns HTTP 200."""
        response = page.goto(f"{base_url}/dam")
        assert response.status == 200

    def test_gallery_has_search_bar(self, page: Page, base_url: str):
        """The gallery has at least one input field."""
        go(page, f"{base_url}/dam")
        assert page.locator("input").count() >= 1

    def test_gallery_has_filters(self, page: Page, base_url: str):
        """The gallery sidebar shows a 'FILTERS' section."""
        go(page, f"{base_url}/dam")
        assert page.get_by_text("FILTERS").count() >= 1


class TestDAMAlbums:
    """Tests for the Albums page at /dam/albums."""

    def test_albums_page_loads(self, page: Page, base_url: str):
        """The /dam/albums page returns HTTP 200."""
        response = page.goto(f"{base_url}/dam/albums")
        assert response.status == 200

    def test_albums_page_has_header(self, page: Page, base_url: str):
        """The Albums page shows 'Albums' as a heading."""
        go(page, f"{base_url}/dam/albums")
        assert page.get_by_text("Albums").count() >= 1

    def test_albums_page_has_new_album_button(self, page: Page, base_url: str):
        """The Albums page has a 'New Album' button."""
        go(page, f"{base_url}/dam/albums")
        expect(page.get_by_text("New Album")).to_be_visible(timeout=10000)


class TestDAMSearch:
    """Tests for the Reverse Image Search page at /dam/search."""

    def test_search_page_loads(self, page: Page, base_url: str):
        """The /dam/search page returns HTTP 200."""
        response = page.goto(f"{base_url}/dam/search")
        assert response.status == 200

    def test_search_page_has_upload_zone(self, page: Page, base_url: str):
        """The search page shows 'Reverse Image Search' heading."""
        go(page, f"{base_url}/dam/search")
        expect(page.get_by_text("Reverse Image Search")).to_be_visible(timeout=10000)


class TestDAMGraphExplorer:
    """Tests for the Visual/Graph Explorer page at /dam/graph."""

    def test_graph_page_loads(self, page: Page, base_url: str):
        """The /dam/graph page returns HTTP 200."""
        response = page.goto(f"{base_url}/dam/graph")
        assert response.status == 200

    def test_graph_page_has_title(self, page: Page, base_url: str):
        """The graph page shows 'KNOWLEDGE GRAPH EXPLORER' heading."""
        go(page, f"{base_url}/dam/graph")
        expect(page.get_by_text("KNOWLEDGE GRAPH EXPLORER")).to_be_visible(timeout=10000)


# =============================================================================
# ADMIN PANEL TESTS
# =============================================================================

class TestAdminPanel:
    """Tests for the admin panel DAM widget integration."""

    def test_admin_page_loads(self, page: Page, base_url: str):
        """The /admin page returns HTTP 200."""
        response = page.goto(f"{base_url}/admin")
        assert response.status == 200

    def test_admin_has_dam_widget(self, page: Page, base_url: str):
        """The Admin Panel shows the DAM Pipeline widget."""
        go(page, f"{base_url}/admin")
        expect(page.get_by_text("DAM Pipeline").first).to_be_visible(timeout=10000)


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

def pytest_configure(config):
    """Register e2e mark."""
    config.addinivalue_line("markers", "e2e: end-to-end tests requiring live server")
