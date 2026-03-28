import re
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 1. Wait until network is idle to ensure all dynamic content is loaded
    page.goto("https://docs.python.org/3/library/asyncio.html", wait_until="networkidle")
    
    # 2. Extract visible text
    raw_text = page.locator("body").inner_text()
    
    # 3. Clean extra whitespace
    clean_text = re.sub(r'\s+', ' ', raw_text).strip()
    
    # 4. Print the FULL text (no character slice)
    print(clean_text)
    
    browser.close()