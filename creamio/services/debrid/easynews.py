import logging
import aiohttp
import base64
from typing import List, Optional
from creamio.services.scrapers.base import ScrapeResult

logger = logging.getLogger(__name__)

class EasynewsClient:
    """
    Easynews API Client.
    """
    BASE_URL = "https://members.easynews.com/2.0/search/solr-search/advanced"

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        auth_str = f"{username}:{password}"
        self.b64_auth = base64.b64encode(auth_str.encode()).decode()
        self.headers = {"Authorization": f"Basic {self.b64_auth}"}

    async def search(self, query: str) -> List[ScrapeResult]:
        """
        Search Easynews and return ScrapeResult objects.
        Note: Easynews results are direct streams, not magnets.
        We hijack the 'magnet' field to store the direct URL for now.
        """
        params = {
            "gps": query,
            "u": "1",
            "fty[]": "VIDEO",
            "fex": "mp4,mkv,avi,wmv,mov"
        }

        results = []
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.BASE_URL, headers=self.headers, params=params) as resp:
                    if resp.status != 200:
                        return []
                    
                    data = await resp.json()
                    items = data.get("data", [])
                    
                    # Global download URL parts from the root response
                    down_url = data.get("downURL")
                    dl_farm = data.get("dlFarm")
                    dl_port = data.get("dlPort")
                    
                    if not (down_url and dl_farm and dl_port):
                        return []
                        
                    url_prefix = f"{down_url}/{dl_farm}/{dl_port}"

                    for item in items:
                        # 0=hash, 10=filename, 11=ext, 4=size(str)
                        post_hash = item.get("0")
                        filename = item.get("10")
                        ext = item.get("11")
                        size_raw = item.get("4", "0")
                        
                        if not (post_hash and filename and ext):
                            continue
                            
                        # Construct URL: prefix/hash.ext/filename.ext
                        # Note: credentials will be injected by the addon frontend/resolver, not here, 
                        # OR we inject them here. 
                        # Security: It's better to inject them only when resolving the stream to user.
                        # But since this is an internal method, we store the CLEAN url.
                        clean_url = f"{url_prefix}/{post_hash}{ext}/{filename}{ext}"
                        
                        # Inject creds for the final stream:
                        # https://user:pass@members.easynews...
                        protocol = "https://"
                        url_body = clean_url.replace("https://", "").replace("http://", "")
                        final_stream_url = f"{protocol}{self.username}:{self.password}@{url_body}"

                        results.append(ScrapeResult(
                            title=filename,
                            infohash="easynews", # dummy hash
                            size=0, # Parsing size string "1.2 GB" is complex, leaving 0 for now
                            seeders=100, # Artificial high number for sorting
                            source="Easynews",
                            magnet=final_stream_url # Storing the direct link in magnet field
                        ))

            except Exception as e:
                logger.error(f"[Easynews] Error: {e}")
                
        return results
