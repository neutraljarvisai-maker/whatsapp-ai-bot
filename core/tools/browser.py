import asyncio
import logging
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class BrowserTool:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate(self, url: str):
        await self.start()
        await self.page.goto(url)
        return f"Navigated to {url}"

    async def search(self, query: str):
        await self.start()
        # Simple search on Google for demo
        await self.page.goto(f"https://www.google.com/search?q={query}")
        return f"Searched for {query}"

    async def get_content(self, max_chars: int = 1000):
        await self.start()
        content = await self.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        return text[:max_chars]

    async def screenshot(self, path: str = "browser_screenshot.png"):
        await self.start()
        await self.page.screenshot(path=path)
        return path
