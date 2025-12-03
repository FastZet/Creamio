import logging
import re
from typing import List
from creamio.services.scrapers.base import BaseScraper, ScrapeResult

logger = logging.getLogger(__name__)

class TorrentGalaxyScraper(BaseScraper):
    def __init__(self, session, user_agent, proxy=None):
        super().__init__(session, user_agent, proxy)
        self.site_name = "TorrentGalaxy"
        self.base_url = "https://torrentgalaxy.to"

    async def scrape(self, query: str) -> List[ScrapeResult]:
        """
        Scrape TorrentGalaxy.
        URL Structure: /torrents.php?search={query}&lang=0&nox=2&sort=seeders&order=desc
        We explicitly set 'c3'=1, 'c4'=1 for XXX categories if possible, 
        but TGx uses 'parent_cat=XXX' in search params commonly.
        """
        # Using specific category IDs for XXX (usually 3, 4, etc.) or just general search
        # c[3]=1 (XXX MP4), c[4]=1 (XXX HD)
        search_url = f"{self.base_url}/torrents.php?search={query}&c3=1&c4=1&sort=seeders&order=desc"
        
        soup = await self.get_soup(search_url)
        if not soup:
            return []

        results = []
        
        try:
            # Rows are class 'tgxtablerow'
            rows = soup.select("div.tgxtable div.tgxtablerow")
            
            for row in rows:
                try:
                    # 1. Title
                    # Inside div.tgxtablecell.clickable-row -> a.txlight
                    title_tag = row.select_one("a[class*='txlight']")
                    if not title_tag:
                        continue
                    title = title_tag["title"]

                    # 2. Magnet & Infohash
                    # Usually a direct magnet button: a[role='button'][href^='magnet:']
                    magnet_tag = row.select_one("a[href^='magnet:']")
                    if not magnet_tag:
                        continue
                    magnet = magnet_tag["href"]
                    
                    hash_match = re.search(r"btih:([a-zA-Z0-9]{40})", magnet)
                    if not hash_match:
                        continue
                    infohash = hash_match.group(1).lower()

                    # 3. Seeders
                    # Seeders are in a span usually colored green or defined column
                    # TGx layout varies, but often it's: font[color='green']
                    seeders_tag = row.select_one("font[color='green']")
                    seeders = int(seeders_tag.text.strip()) if seeders_tag else 0

                    # 4. Size
                    # Size is often in a span class 'badge' or just text in a cell
                    # We look for the cell that contains file size format
                    size_tag = row.select_one("span.badge.badge-secondary")
                    size = 0
                    if size_tag:
                        size_text = size_tag.text.strip()
                        if "GB" in size_text:
                            size = int(float(size_text.replace("GB", "").strip()) * 1024**3)
                        elif "MB" in size_text:
                            size = int(float(size_text.replace("MB", "").strip()) * 1024**2)

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
