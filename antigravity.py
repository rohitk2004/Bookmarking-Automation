
import asyncio
import random
from playwright.async_api import async_playwright

class AntigravityWrapper:
    def __init__(self):
        self._playwright = None
        self._browser = None

    async def launch(self, headless=False, proxy=None):
        """
        Launches the browser with optional proxy and random user-agent.
        """
        self._playwright = await async_playwright().start()
        
        # Random User Agent List
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
             "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        ]
        
        launch_args = []
        if proxy:
            launch_args.append(f"--proxy-server={proxy}")

        self._browser = await self._playwright.chromium.launch(
            headless=headless,
            args=launch_args
        )
        return self._browser

    def run(self, coro):
        """
        Runs the async main loop.
        """
        try:
            asyncio.run(coro)
        except KeyboardInterrupt:
            pass
        finally:
            pass

# Create a singleton instance to emulate the module-level access pattern
_instance = AntigravityWrapper()
launch = _instance.launch
run = _instance.run
