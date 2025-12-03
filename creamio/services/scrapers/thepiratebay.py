import logging
import re
from typing import List
from creamio.services.scrapers.base import BaseScraper, ScrapeResult

logger = logging.getLogger(__name__)

class ThePirateBayScraper(BaseScraper):
    def __init__(self, session, user_agent, proxy=None):
        super().__init__(session, user_agent, proxy)
        self.site_name = "ThePirateBay"
        # We use a reliable proxy mirror if the main site is down, 
        # but ideally this base URL should be configurable or rotated.
        self.base_url = "https://tpb.party" 

    async def scrape(self, query: str) -> List[ScrapeResult]:
        """
        Scrape TPB for the query in the Porn category (500).
        """
        # URL Pattern: /search/{query}/{page}/7/500
        # 7 = Sort by seeders desc
        # 500 = Porn category
        search_url = f"{self.base_url}/search/{query}/1/7/500"
        
        soup = await self.get_soup(search_url)
        if not soup:
            return []

        results = []
        
        try:
            # TPB table rows are usually <tr class="header">...</tr> followed by data rows
            # We skip the header
            rows = soup.select("table#searchResult tr:not(.header)")
            
            for row in rows:
                try:
                    # 1. Title
                    title_tag = row.select_one("div.detName a")
                    if not title_tag:
                        continue
                    title = title_tag.text.strip()

                    # 2. Magnet & Infohash
                    # The magnet link is usually the second 'a' tag in the second 'td' or explicitly select by href^="magnet:"
                    magnet_tag = row.select_one("a[href^='magnet:']")
                    if not magnet_tag:
                        continue
                    magnet = magnet_tag["href"]
                    
                    # Extract infohash from magnet link (btih:HASH)
                    # Standard regex for 40-char hex string
                    hash_match = re.search(r"btih:([a-zA-Z0-9]{40})", magnet)
                    if not hash_match:
                        continue
                    infohash = hash_match.group(1).lower()

                    # 3. Seeders
                    # Seeders are in the 3rd column (td aligned right)
                    tds = row.find_all("td")
                    if len(tds) < 3:
                        continue
                    seeders = int(tds[2].text.strip())

                    # 4. Size
                    # Size is inside a font tag with class 'detDesc', e.g. "Uploaded 02-28 2009, Size 209.88 MiB, ULed by..."
                    # We parse this loosely or use 0 if complex
                    desc_tag = row.select_one("font.detDesc")
                    size = 0
                    if desc_tag:
                        desc_text = desc_tag.text
                        # Regex to find "Size 123.45 MiB"
                        size_match = re.search(r"Size ([\d\.]+)\s([KMGT]i?B)", desc_text)
                        if size_match:
                            val = float(size_match.group(1))
                            unit = size_match.group(2)
                            # Simple converter
                            multipliers = {'KiB': 1024, 'MiB': 1024**2, 'GiB': 1024**3, 'TiB': 1024**4}
                            size = int(val * multipliers.get(unit, 1))

                    results.append(ScrapeResult(
                        title=title,
                        infohash=infohash,
                        magnet=magnet,
                        seeders=seeders,
                        size=size,
                        source=self.site_name
                    ))

                except Exception as e:
                    logger.debug(f"[{self.site_name}] Error parsing row: {e}")
                    continue

        except Exception as e:
            logger.error(f"[{self.site_name}] Parse error: {e}")

        logger.info(f"[{self.site_name}] Found {len(results)} results for '{query}'")
        return results
