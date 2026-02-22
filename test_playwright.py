from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        print("Launching Chromium...")
        browser = p.chromium.launch(headless=False)
        print("Browser launched successfully!")
        page = browser.new_page()
        page.goto("https://example.com")
        print("Page title:", page.title())
        browser.close()

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print("ERROR:", e)
