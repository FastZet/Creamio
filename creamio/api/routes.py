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
        # Fix padding if needed
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
        "version": "1.0.0",
        "name": "Creamio",
        "description": "Adult Content via StashDB + Debrid",
        "types": ["movie"],
        "catalogs": [{"type": "movie", "id": "stashdb_trending", "name": "StashDB Trending"}],
        "resources": ["catalog", "meta", "stream"],
        "idPrefixes": ["stashdb:"]
    }

@router.get("/{config}/catalog/{type}/{id}.json")
async def catalog(config: str, type: str, id: str):
    if id != "stashdb_trending": return {"metas": []}
    
    client = StashDBClient()
    scenes = await client.search_scenes("", page=1)
    
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

@router.get("/{config}/meta/{type}/{id}.json")
async def meta(config: str, type: str, id: str):
    real_id = id.replace("stashdb:", "")
    client = StashDBClient()
    scene = await client.get_scene(real_id)
    if not scene: return {"meta": {}}
    
    img = scene["images"][0]["url"] if scene.get("images") else None
    return {"meta": {
        "id": id,
        "type": "movie",
        "name": scene.get("title"),
        "poster": img,
        "background": img,
        "description": scene.get("details"),
        "cast": [p["name"] for p in scene.get("performers", [])]
    }}

@router.get("/{config}/stream/{type}/{id}.json")
async def stream(request: Request, config: str, type: str, id: str):
    conf = parse_config(config)
    real_id = id.replace("stashdb:", "")
    
    client = StashDBClient()
    scene = await client.get_scene(real_id)
    if not scene: return {"streams": []}
    
    # Build Query
    query = scene['title']
    # Only add performers if title is short/generic, otherwise it dilutes the search
    if len(query) < 10 and scene.get("performers"):
        query += " " + " ".join([p["name"] for p in scene["performers"]])
    
    streams = []
    base_url = str(request.base_url).rstrip("/")

    # --- Easynews ---
    if conf.get("easynews_user") and conf.get("easynews_pass"):
        try:
            en = EasynewsClient(conf["easynews_user"], conf["easynews_pass"])
            en_results = await en.search(query)
            for res in en_results:
                streams.append({
                    "name": "[EN] Easynews",
                    "title": f"{res.title}\nDirect Stream",
                    "url": res.magnet
                })
        except Exception as e:
            logger.error(f"Easynews Error: {e}")

    # --- Scrapers (Shared for RD/TorBox) ---
    # Only scrape if we have a Debrid service configured
    if conf.get("rd_key") or conf.get("torbox_key"):
        scraper_mgr = ScraperManager()
        cached = await get_cached_search(query)
        
        if cached:
            torrents = cached
        else:
            scrape_results = await scraper_mgr.search(query)
            torrents = [r.model_dump() for r in scrape_results]
            await cache_search_results(query, torrents)
        
        # --- Real Debrid ---
        if conf.get("rd_key"):
            try:
                rd = RealDebrid(conf["rd_key"])
                hashes = [t["infohash"] for t in torrents if t["source"] != "Easynews"]
                availability = await rd.check_availability(hashes)
                
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
            except Exception as e:
                logger.error(f"RD Error: {e}")

        # --- TorBox ---
        if conf.get("torbox_key"):
            try:
                tb = TorBox(conf["torbox_key"])
                # TorBox doesn't have a bulk 'check_availability' exactly like RD
                # But we can just list them. 
                # We mark them as [TB]
                
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
            except Exception as e:
                 logger.error(f"TorBox Error: {e}")
            
    return {"streams": streams}

# --- Resolve Routes ---

@router.get("/resolve/rd/{token}/{infohash}/{b64_magnet}")
async def resolve_rd(token: str, infohash: str, b64_magnet: str):
    try:
        magnet = base64.urlsafe_b64decode(b64_magnet).decode()
        rd = RealDebrid(token)
        link = await rd.resolve_stream(magnet, infohash)
        if link: return RedirectResponse(link)
    except Exception as e:
        logger.error(f"RD Resolve Error: {e}")
    return JSONResponse({"error": "Failed"}, status_code=404)

@router.get("/resolve/tb/{token}/{infohash}/{b64_magnet}")
async def resolve_tb(token: str, infohash: str, b64_magnet: str):
    try:
        magnet = base64.urlsafe_b64decode(b64_magnet).decode()
        tb = TorBox(token)
        link = await tb.resolve_stream(magnet, infohash)
        if link: return RedirectResponse(link)
    except Exception as e:
        logger.error(f"TB Resolve Error: {e}")
    return JSONResponse({"error": "Failed"}, status_code=404)
