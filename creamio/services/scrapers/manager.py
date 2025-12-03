import asyncio
import logging
from typing import List

import aiohttp
from rapidfuzz import fuzz, process

from creamio.core.settings import get_settings
from creamio.services.scrapers.base import ScrapeResult
from creamio.services.scrapers.thepiratebay import ThePirateBayScraper
from creamio.services.scrapers.x1337 import X1337Scraper
from creamio.services.scrapers.torrentgalaxy import TorrentGalaxyScraper

logger = logging.getLogger(__name__)
settings = get_settings()

class ScraperManager:
    """
    Orchestrates multiple scrapers in parallel and aggregates results.
    """
    
    def __init__(self):
        self.scrapers = [
            ThePirateBayScraper,
            X1337Scraper,
            TorrentGalaxyScraper
        ]

    async def search(self, query: str, limit: int = 20) -> List[ScrapeResult]:
        """
        Run all scrapers for the given query.
        
        Args:
            query: Search term (e.g. "Riley Reid Blacked")
            limit: Max results to return
        """
        results: List[ScrapeResult] = []
        
        async with aiohttp.ClientSession() as session:
            # Initialize all scraper instances
            scraper_instances = [
                cls(
                    session=session, 
                    user_agent=settings.USER_AGENT,
                    proxy=settings.SCRAPE_PROXY
                ) 
                for cls in self.scrapers
            ]
            
            # Run .scrape() for all of them concurrently
            # return_exceptions=True prevents one scraper from crashing the whole batch
            tasks = [
                scraper.scrape(query) 
                for scraper in scraper_instances
            ]
            
            logger.info(f"Starting scraping for: {query}")
            all_results_raw = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Flatten list and handle exceptions
            for res in all_results_raw:
                if isinstance(res, list):
                    results.extend(res)
                elif isinstance(res, Exception):
                    logger.error(f"Scraper task failed: {res}")

        # Deduplicate by Infohash
        unique_results = {}
        for r in results:
            # If duplicate, keep the one with more seeders
            if r.infohash in unique_results:
                if r.seeders > unique_results[r.infohash].seeders:
                    unique_results[r.infohash] = r
            else:
                unique_results[r.infohash] = r
        
        final_results = list(unique_results.values())

        # Sort by fuzzy match relevance + seeders
        # We give 70% weight to fuzzy match score and 30% to seeders (normalized)
        if final_results:
            # Pre-calculate fuzzy scores
            for res in final_results:
                # Simple token_set_ratio handles partial matches well
                score = fuzz.token_set_ratio(query.lower(), res.title.lower())
                # Store score temporarily on object (dynamic attribute)
                setattr(res, "_score", score)
            
            # Sort descending
            final_results.sort(
                key=lambda x: (getattr(x, "_score", 0), x.seeders), 
                reverse=True
            )

        logger.info(f"Aggregated {len(final_results)} unique results for '{query}'")
        return final_results[:limit]
