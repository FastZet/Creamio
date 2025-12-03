import logging
from abc import ABC, abstractmethod
from typing import List, Optional

import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ScrapeResult(BaseModel):
    """
    Standardized format for a scraped torrent result.
    """
    title: str
    infohash: str
    size: int = 0          # Size in bytes
    seeders: int = 0       # Number of seeders
    source: str            # The name of the site (e.g., "ThePirateBay")
    magnet: Optional[str] = None  # Optional full magnet link


class BaseScraper(ABC):
    """
    Abstract Base Class that all specific site scrapers must implement.
    This ensures every scraper has a .scrape() method.
    """

    def __init__(self, session: aiohttp.ClientSession, user_agent: str, proxy: str = None):
        """
        Initialize with a shared HTTP session to reuse connections.
        
        Args:
            session: The aiohttp session
            user_agent: The spoofed user agent string
            proxy: Optional proxy URL for requests
        """
        self.session = session
        self.headers = {"User-Agent": user_agent}
        self.proxy = proxy
        self.site_name = "Generic"

    async def get_soup(self, url: str):
        """
        Helper method to fetch a URL and return BeautifulSoup object.
        Useful for HTML parsing.
        """
        from bs4 import BeautifulSoup

        try:
            async with self.session.get(
                url, 
                headers=self.headers, 
                proxy=self.proxy, 
                timeout=15
            ) as response:
                if response.status != 200:
                    logger.warning(f"[{self.site_name}] Failed to fetch {url}: Status {response.status}")
                    return None
                
                html = await response.text()
                return BeautifulSoup(html, "lxml")
        except Exception as e:
            logger.error(f"[{self.site_name}] Connection error: {e}")
            return None

    @abstractmethod
    async def scrape(self, query: str) -> List[ScrapeResult]:
        """
        The main method to implement.
        Must take a string query and return a list of ScrapeResult objects.
        """
        pass
