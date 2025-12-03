import logging
import aiohttp
from typing import List, Dict, Optional
from creamio.services.scrapers.base import ScrapeResult

logger = logging.getLogger(__name__)

class TorBox:
    """
    TorBox API Client.
    Docs: https://torbox.app/api
    """
    BASE_URL = "https://api.torbox.app/v1/api"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def search_internal(self, query: str) -> List[ScrapeResult]:
        """
        Use TorBox's internal search to find cached content directly.
        """
        url = f"{self.BASE_URL}/torrents/search"
        params = {"query": query}
        
        results = []
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as resp:
                    if resp.status != 200:
                        return []
                    
                    data = await resp.json()
                    # Parse TorBox specific response structure
                    # This structure assumes standard TorBox output, may need adjustment
                    items = data.get("data", [])
                    for item in items:
                        results.append(ScrapeResult(
                            title=item.get("name", "Unknown"),
                            infohash=item.get("hash", ""),
                            size=item.get("size", 0),
                            seeders=item.get("seeds", 0),
                            source="TorBoxCache",
                            magnet=None # Usually not needed if we have hash + it's cached
                        ))
            except Exception as e:
                logger.error(f"[TorBox] Search error: {e}")
                
        return results

    async def resolve_stream(self, magnet: str, infohash: str) -> Optional[str]:
        """
        Get a streamable URL from TorBox.
        1. Add Torrent/Magnet
        2. Request link
        """
        async with aiohttp.ClientSession() as session:
            try:
                # 1. Create Torrent
                create_url = f"{self.BASE_URL}/torrents/create"
                form_data = {"magnet": magnet, "seed": "1", "allow_zip": "false"}
                
                async with session.post(create_url, headers=self.headers, data=form_data) as resp:
                    if resp.status != 200:
                        logger.error(f"[TorBox] Failed to add magnet: {await resp.text()}")
                        return None
                    
                    data = await resp.json()
                    # Data should contain the torrent_id or a success message
                    # If it's already cached, it might return success immediately
                    
                    if not data.get("success"):
                         return None

                    torrent_id = data.get("data", {}).get("torrent_id")
                    if not torrent_id:
                        # Sometimes it returns the ID directly or in a different field
                        return None

                # 2. Get Request Link (Unrestrict)
                # In TorBox, we ask for the download link of the file
                # First we need to list the files to find the video
                info_url = f"{self.BASE_URL}/torrents/mylist"
                async with session.get(info_url, headers=self.headers) as resp:
                    mylist = await resp.json()
                    
                # Find our torrent in the list
                target = next((t for t in mylist.get("data", []) if t["id"] == torrent_id), None)
                
                if not target:
                    return None
                    
                # Get the first file ID (assuming single video file for simplicity)
                files = target.get("files", [])
                if not files:
                    return None
                    
                file_id = files[0]["id"]
                
                # 3. Request Download Link
                link_url = f"{self.BASE_URL}/torrents/requestdl"
                async with session.get(link_url, headers=self.headers, params={"token": self.api_key, "torrent_id": torrent_id, "file_id": file_id}) as resp:
                     if resp.status != 200:
                         return None
                     link_data = await resp.json()
                     return link_data.get("data")

            except Exception as e:
                logger.error(f"[TorBox] Resolve error: {e}")
                return None
