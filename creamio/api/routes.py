import base64
import json
import logging
from urllib.parse import quote, unquote

from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from creamio.core.settings import get_settings
from creamio.services.stashdb import StashDBClient
from creamio.services.scrapers.manager import ScraperManager
from creamio.services.debrid.realdebrid import RealDebrid
from creamio.services.debrid.torbox import TorBox
from creamio.services.debrid.easynews import EasynewsClient
from creamio.db.database import get_cached_search, cache_search_results

router = APIRouter()
settings = get_settings()
templates = Jinja2Templates(directory="creamio/templates")
logger = logging.getLogger(__name__)

def parse_config(b64_config: str) -> dict:
    try:
        padding = len(b64_config) % 4
        if padding:
            b64_config += "=" * (4 - padding)
        return json.loads(base64.b64decode(b64_config).decode("utf-8"))
    except Exception as e:
        logger.error(f"Config Parse Error: {e}")
        return {}

@router.get("/")
async def root():
    return RedirectResponse("/configure")

@router.get("/configure")
async def configure(request: Request):
    return templates.TemplateResponse("config.html", {"request": request})

@router.get("/manifest.json")
@router.get("/{config}/manifest.json")
async def manifest(config: str = None):
    return {
        "id": "com.creamio.addon",
        "version": "1.0.2",
        "name": "Creamio",
        "description": "Adult Content via StashDB + Debrid",
        "types": ["movie"],
        "catalogs": [
            {
                "type": "movie", 
                "id": "stashdb_search", 
                "name": "StashDB", 
                "extra": [{"name": "search", "isRequired": False}]
            }
        ],
        "resources": ["catalog", "meta", "stream"],
        "idPrefixes": ["stashdb:"]
    }

@router.get("/{config}/catalog/{type}/{id}.json")
@router.get("/{config}/catalog/{type}/{id}/{extra}.json")
async def catalog(config: str, type: str, id: str, extra: str = None):
    """
    Handles both 'Trending' (no extra) and 'Search' (extra=search=...)
    """
    logger.info(f"[Catalog] Request: type={type}, id={id}, extra={extra}")
    
    if id != "stashdb_search":
        return {"metas": []}

    client = StashDBClient()
    scenes = []
    search_query = ""

    # Robust 'extra' parsing
    if extra:
        try:
            # Stremio often sends extra as: "search=term"
            # or "genre=something&search=term"
            params = extra.split("&")
            for param in params:
                if param.startswith("search="):
                    raw_query = param.split("search=")[1]
                    search_query = unquote(raw_query)
                    break
        except Exception as e:
            logger.error(f"[Catalog] Failed to parse extra args: {e}")

    if search_query:
        logger.info(f"[Catalog] Searching StashDB for: '{search_query}'")
        
        # 1. Try to find Performer first (High priority for "Mia Malkova")
        performer_scenes = await client.get_performer_scenes(search_query)
        
        if performer_scenes:
            logger.info(f"[Catalog] Found {len(performer_scenes)} scenes via Performer lookup")
            scenes = performer_scenes
        else:
            # 2. Fallback to scene title search
            logger.info(f"[Catalog] Performer lookup empty. Searching scene titles...")
            scenes = await client.search_scenes(search_query)
    else:
        # No search query = Trending
        logger.info("[Catalog] Fetching Trending Scenes")
        scenes = await client.search_scenes("", page=1)
    
    logger.info(f"[Catalog] Returning {len(scenes)} items")

    metas = []
    for s in scenes:
        img = s["images"][0]["url"] if s.get("images") else None
        metas.append({
            "id": f"stashdb:{s['id']}",
            "type": "movie",
            "name": s.get("title", "Unknown"),
            "poster": img,
            "description": s.get("details")
        })
    return {"metas": metas}

# ... Meta and Stream endpoints remain the same (they were correct) ...
# (Include the rest of the file as previously provided)
@router.get("/{config}/meta/{type}/{id}.json")
async def meta(config: str, type: str, id: str):
    logger.info(f"[Meta] Request for {id}")
    real_id = id.replace("stashdb:", "")
    client = StashDBClient()
    scene = await client.get_scene(real_id)
    
    if not scene: 
        logger.warning(f"[Meta] Scene not found in StashDB: {real_id}")
        return {"meta": {}}
    
    img = scene["images"][0]["url"] if scene.get("images") else None
    return {"meta": {
        "id": id,
        "type": "movie",
        "name": scene.get("title"),
        "poster": img,
        "background": img,
        "description": scene.get("details"),
        "cast": [p["name"] for p in scene.get("performers", [])],
        "director": [scene["studio"]["name"]] if scene.get("studio") else []
    }}

@router.get("/{config}/stream/{type}/{id}.json")
async def stream(request: Request, config: str, type: str, id: str):
    logger.info(f"[Stream] Request for {id}")
    conf = parse_config(config)
    real_id = id.replace("stashdb:", "")
    
    client = StashDBClient()
    scene = await client.get_scene(real_id)
    if not scene: 
        logger.error(f"[Stream] Scene metadata lookup failed for {real_id}")
        return {"streams": []}
    
    # Build Query
    query = scene['title']
    if len(query) < 10 and scene.get("performers"):
        query += " " + " ".join([p["name"] for p in scene["performers"]])
    
    logger.info(f"[Stream] Generated Search Query: '{query}'")
    
    streams = []
    base_url = str(request.base_url).rstrip("/")

    # --- Easynews ---
    if conf.get("easynews_user") and conf.get("easynews_pass"):
        try:
            logger.info("[Stream] Searching Easynews...")
            en = EasynewsClient(conf["easynews_user"], conf["easynews_pass"])
            en_results = await en.search(query)
            logger.info(f"[Stream] Easynews found {len(en_results)} results")
            for res in en_results:
                streams.append({
                    "name": "[EN] Easynews",
                    "title": f"{res.title}\nDirect Stream",
                    "url": res.magnet
                })
        except Exception as e:
            logger.error(f"[Stream] Easynews Error: {e}")

    # --- Scrapers ---
    if conf.get("rd_key") or conf.get("torbox_key"):
        logger.info("[Stream] Checking Cache for torrents...")
        scraper_mgr = ScraperManager()
        cached = await get_cached_search(query)
        
        if cached:
            logger.info(f"[Stream] Cache Hit: {len(cached)} torrents found")
            torrents = cached
        else:
            logger.info("[Stream] Cache Miss: Starting Scrapers...")
            scrape_results = await scraper_mgr.search(query)
            torrents = [r.model_dump() for r in scrape_results]
            await cache_search_results(query, torrents)
            logger.info(f"[Stream] Scraped {len(torrents)} new torrents")
        
        # --- Real Debrid ---
        if conf.get("rd_key"):
            try:
                logger.info("[Stream] Checking RealDebrid Availability...")
                rd = RealDebrid(conf["rd_key"])
                hashes = [t["infohash"] for t in torrents if t["source"] != "Easynews"]
                availability = await rd.check_availability(hashes)
                
                rd_count = 0
                for t in torrents:
                    if t["source"] == "Easynews": continue
                    h = t["infohash"]
                    is_cached = availability.get(h, False)
                    
                    title = f"{'[RD+]' if is_cached else '[RD]'} {t['title']}\n💾 {t['size']/1024/1024:.0f}MB 👤 {t['seeders']}"
                    b64_magnet = base64.urlsafe_b64encode(t["magnet"].encode()).decode()
                    
                    streams.append({
                        "name": f"RD {t['source']}",
                        "title": title,
                        "url": f"{base_url}/resolve/rd/{conf['rd_key']}/{h}/{b64_magnet}"
                    })
                    rd_count += 1
                logger.info(f"[Stream] Added {rd_count} RD streams")
            except Exception as e:
                logger.error(f"[Stream] RD Error: {e}")

        # --- TorBox ---
        if conf.get("torbox_key"):
            try:
                logger.info("[Stream] Processing TorBox results...")
                # TB Logic...
                tb_count = 0
                for t in torrents:
                    if t["source"] == "Easynews": continue
                    h = t["infohash"]
                    title = f"[TB] {t['title']}\n💾 {t['size']/1024/1024:.0f}MB 👤 {t['seeders']}"
                    b64_magnet = base64.urlsafe_b64encode(t["magnet"].encode()).decode()
                    streams.append({
                        "name": f"TB {t['source']}",
                        "title": title,
                        "url": f"{base_url}/resolve/tb/{conf['torbox_key']}/{h}/{b64_magnet}"
                    })
                    tb_count += 1
                logger.info(f"[Stream] Added {tb_count} TorBox streams")
            except Exception as e:
                 logger.error(f"[Stream] TorBox Error: {e}")
            
    logger.info(f"[Stream] Total streams returned: {len(streams)}")
    return {"streams": streams}

@router.get("/resolve/rd/{token}/{infohash}/{b64_magnet}")
async def resolve_rd(token: str, infohash: str, b64_magnet: str):
    logger.info(f"[Resolve] RD Request for hash {infohash}")
    try:
        magnet = base64.urlsafe_b64decode(b64_magnet).decode()
        rd = RealDebrid(token)
        link = await rd.resolve_stream(magnet, infohash)
        if link: 
            logger.info("[Resolve] Success -> Redirecting")
            return RedirectResponse(link)
        logger.warning("[Resolve] Failed to get link from RD")
    except Exception as e:
        logger.error(f"[Resolve] RD Error: {e}")
    return JSONResponse({"error": "Failed"}, status_code=404)

@router.get("/resolve/tb/{token}/{infohash}/{b64_magnet}")
async def resolve_tb(token: str, infohash: str, b64_magnet: str):
    logger.info(f"[Resolve] TorBox Request for hash {infohash}")
    try:
        magnet = base64.urlsafe_b64decode(b64_magnet).decode()
        tb = TorBox(token)
        link = await tb.resolve_stream(magnet, infohash)
        if link: 
            logger.info("[Resolve] Success -> Redirecting")
            return RedirectResponse(link)
        logger.warning("[Resolve] Failed to get link from TorBox")
    except Exception as e:
        logger.error(f"[Resolve] TorBox Error: {e}")
    return JSONResponse({"error": "Failed"}, status_code=404)
