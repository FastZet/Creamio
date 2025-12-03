import logging
import aiohttp
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class RealDebrid:
    """
    Real Debrid API Client.
    """
    BASE_URL = "https://api.real-debrid.com/rest/1.0"

    def __init__(self, api_key: str, ip: str = None):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
        # RD requires strictly no simultaneous requests from different IPs on same token
        # We pass the user's IP if needed for proxies, but usually for Addons the server IP is fine
        # unless we are proxying the stream.

    async def check_availability(self, infohashes: List[str]) -> Dict[str, bool]:
        """
        Check if torrents are instantly available on RD servers.
        API Endpoint: /torrents/instantAvailability/{hash1}/{hash2}...
        """
        if not infohashes:
            return {}

        # RD limits URL length, so we batch requests (e.g. 20 hashes at a time)
        available_hashes = {}
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(infohashes), 20):
                batch = infohashes[i:i+20]
                url = f"{self.BASE_URL}/torrents/instantAvailability/{'/'.join(batch)}"
                
                try:
                    async with session.get(url, headers=self.headers) as response:
                        if response.status != 200:
                            logger.warning(f"[RealDebrid] Availability check failed: {response.status}")
                            continue
                        
                        data = await response.json()
                        
                        # Parse response.
                        # Format: { "hash": { "rd": [ { "filename": "...", "filesize": ... } ] } }
                        # If "rd" key exists and is not empty, it is cached.
                        for h in batch:
                            h = h.lower()
                            if h in data and "rd" in data[h] and data[h]["rd"]:
                                available_hashes[h] = True
                            else:
                                available_hashes[h] = False
                                
                except Exception as e:
                    logger.error(f"[RealDebrid] Error checking availability: {e}")

        return available_hashes

    async def resolve_stream(self, magnet: str, infohash: str) -> Optional[str]:
        """
        Convert a magnet link or infohash into a streamable URL.
        1. Add magnet to RD
        2. Select all files
        3. Get the download link
        4. Unrestrict the link
        """
        async with aiohttp.ClientSession() as session:
            try:
                # 1. Add Magnet
                add_url = f"{self.BASE_URL}/torrents/addMagnet"
                async with session.post(add_url, headers=self.headers, data={"magnet": magnet}) as resp:
                    if resp.status != 201:
                        logger.error(f"[RealDebrid] Failed to add magnet: {resp.status}")
                        return None
                    data = await resp.json()
                    torrent_id = data["id"]

                # 2. Select Files (We select 'all' to ensure we get the video)
                select_url = f"{self.BASE_URL}/torrents/selectFiles/{torrent_id}"
                async with session.post(select_url, headers=self.headers, data={"files": "all"}) as resp:
                    if resp.status not in (202, 204):
                         logger.error(f"[RealDebrid] Failed to select files: {resp.status}")

                # 3. Get Torrent Info (to get the link)
                info_url = f"{self.BASE_URL}/torrents/info/{torrent_id}"
                async with session.get(info_url, headers=self.headers) as resp:
                    info = await resp.json()
                
                if not info.get("links"):
                    return None
                
                # We typically take the largest file or the first one
                # For simplicity, we take the first generated link
                link_to_unrestrict = info["links"][0]

                # 4. Unrestrict Link
                unrestrict_url = f"{self.BASE_URL}/unrestrict/link"
                async with session.post(unrestrict_url, headers=self.headers, data={"link": link_to_unrestrict}) as resp:
                    if resp.status != 200:
                        return None
                    item = await resp.json()
                    return item["download"]

            except Exception as e:
                logger.error(f"[RealDebrid] Resolve error: {e}")
                return None
