from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json
import base64
import aiohttp

from stash_api import get_scenes, get_scene_meta # Import our new function

# --- (addon_manifest remains the same) ---
addon_manifest = {
    "id": "org.stremio.stashdb",
    "version": "1.0.3",
    "name": "StashDB Catalog",
    "description": "Provides an adult content catalog from StashDB.org for Stremio.",
    "resources": ["catalog", "meta"],
    "types": ["movie", "series"], 
    "catalogs": [
        { "type": "movie", "id": "stashdb_scenes", "name": "StashDB Scenes" },
        { "type": "series", "id": "stashdb_performers", "name": "StashDB Performers (Coming Soon)" }
    ],
    "logo": "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/favicon-32x32.png",
    "background": "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/stash-logo-horizontal-dark.png",
    "behaviorHints": { "configurable": True, "configurationRequired": True }
}

app = FastAPI( title=addon_manifest["name"], version=addon_manifest["version"],)
templates = Jinja2Templates(directory="templates")

def decode_config(b64_config: str) -> dict:
    try:
        decoded_bytes = base64.b64decode(b64_config)
        return json.loads(decoded_bytes.decode('utf-8'))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid configuration format")

# --- Endpoints ---

@app.get("/", response_class=HTMLResponse)
@app.get("/configure", response_class=HTMLResponse)
async def configure(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/{b64_config}/manifest.json")
async def get_configured_manifest(b64_config: str):
    decode_config(b64_config)
    return Response(content=json.dumps(addon_manifest), media_type="application/json")

@app.get("/{b64_config}/catalog/{catalog_type}/{catalog_id}.json")
async def get_catalog(b64_config: str, catalog_type: str, catalog_id: str):
    config = decode_config(b64_config)
    api_key = config.get("stash_api_key")
    if not api_key:
        raise HTTPException(status_code=403, detail="API key is missing")
    metas = []
    async with aiohttp.ClientSession() as session:
        if catalog_id == "stashdb_scenes":
            metas = await get_scenes(session, api_key)
    return {"metas": metas}

# --- NEW ENDPOINT STARTS HERE ---

@app.get("/{b64_config}/meta/{meta_type}/{meta_id}.json")
async def get_meta(b64_config: str, meta_type: str, meta_id: str):
    config = decode_config(b64_config)
    api_key = config.get("stash_api_key")
    if not api_key:
        raise HTTPException(status_code=403, detail="API key is missing")

    # Stremio will give us an ID like "stashdb:scene:xxxx". We need to extract the "xxxx" part.
    id_parts = meta_id.split(':')
    if id_parts[0] != "stashdb" or len(id_parts) < 3:
        raise HTTPException(status_code=400, detail="Invalid StashDB ID format")
    
    content_type = id_parts[1]
    content_id = id_parts[2]
    
    meta_data = None
    async with aiohttp.ClientSession() as session:
        if content_type == "scene":
            meta_data = await get_scene_meta(session, api_key, content_id)

    if not meta_data:
        raise HTTPException(status_code=404, detail=f"{content_type.capitalize()} not found")

    return meta_data
