import logging
import re
from typing import List
from creamio.services.scrapers.base import BaseScraper, ScrapeResult

logger = logging.getLogger(__name__)

class X1337Scraper(BaseScraper):
    def __init__(self, session, user_agent, proxy=None):
        super().__init__(session, user_agent, proxy)
        self.site_name = "1337x"
        self.base_url = "https://1337x.to"

    async def _get_magnet_link(self, torrent_url: str) -> str | None:
        """
        1337x doesn't list magnets in the search results.
        We must fetch the detail page for each result to get the magnet.
        This is slower, so we only do it for the top few matches.
        """
        # Fix URL if relative
        if torrent_url.startswith("/"):
            torrent_url = f"{self.base_url}{torrent_url}"
            
        soup = await self.get_soup(torrent_url)
        if not soup:
            return None
            
        # Magnet link is usually in a predefined list or button
        # Look for a[href^="magnet:"]
        magnet_tag = soup.select_one("a[href^='magnet:']")
        if magnet_tag:
            return magnet_tag["href"]
            
        return None

    async def scrape(self, query: str) -> List[ScrapeResult]:
        """
        Scrape 1337x for the query in the XXX category.
        URL Structure: /category-search/{query}/XXX/1/
        """
        search_url = f"{self.base_url}/category-search/{query}/XXX/1/"
        
        soup = await self.get_soup(search_url)
        if not soup:
            return []

        results = []
        
        try:
            # Table rows in tbody
            rows = soup.select("table.table-list tbody tr")
            
            # Limit to top 5 to avoid too many sub-requests for magnets
            for row in rows[:5]:
                try:
                    # 1. Title and Detail URL
                    # The title is in the second 'a' tag inside class 'name'
                    name_col = row.select_one("td.name")
                    if not name_col:
                        continue
                        
                    links = name_col.select("a")
                    if len(links) < 2:
                        continue
                        
                    # links[1] is usually the torrent link, links[0] is icon?
                    detail_href = links[1]["href"]
                    title = links[1].text.strip()

                    # 2. Seeders (td class 'seeds')
                    seeds_tag = row.select_one("td.seeds")
                    seeders = int(seeds_tag.text.strip()) if seeds_tag else 0

                    # 3. Size (td class 'size')
                    size_tag = row.select_one("td.size")
                    size = 0
                    if size_tag:
                        # Format: "1.2 GB <span..." -> get just text node
                        size_text = size_tag.contents[0].strip() if size_tag.contents else ""
                        if "GB" in size_text:
                            size = int(float(size_text.replace("GB", "").strip()) * 1024**3)
                        elif "MB" in size_text:
                            size = int(float(size_text.replace("MB", "").strip()) * 1024**2)

                    # 4. Get Magnet (Sub-request)
                    magnet = await self._get_magnet_link(detail_href)
                    if not magnet:
                        continue

                    # 5. Extract Hash
                    hash_match = re.search(r"btih:([a-zA-Z0-9]{40})", magnet)
                    if not hash_match:
                        continue
                    infohash = hash_match.group(1).lower()

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
