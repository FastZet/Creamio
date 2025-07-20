from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import json
import base64
import aiohttp
from urllib.parse import unquote

from stash_api import get_scenes, get_scene_meta, search_scenes, search_performers

addon_manifest = {
    "id": "org.stremio.stashdb",
    "version": "1.1.1", # Version bump
    "name": "StashDB Catalog",
    "description": "Provides an adult content catalog from StashDB.org for Stremio.",
    "resources": ["catalog", "meta"],
    "types": ["movie", "series"], 
    "catalogs": [
        { "type": "movie", "id": "stashdb_scenes", "name": "StashDB Scenes", "extra": [ { "name": "search", "isRequired": False } ] },
        { "type": "series", "id": "stashdb_performers", "name": "StashDB Performers", "extra": [ { "name": "search", "isRequired": False } ] }
    ],
    "logo": "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/favicon-32x32.png",
    "background": "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/stash-logo-horizontal-dark.png",
    "behaviorHints": { "configurable": True, "configurationRequired": False }
}

app = FastAPI(title=addon_manifest["name"], version=addon_manifest["version"])
templates = Jinja2Templates(directory="templates")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def decode_config(b64_config: str) -> dict:
    try:
        return json.loads(base64.b64decode(b64_config).decode('utf-8'))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid configuration format")

@app.get("/", response_class=HTMLResponse)
@app.get("/configure", response_class=HTMLResponse)
async def configure(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "api_key": ""})

@app.get("/{b64_config}/configure", response_class=HTMLResponse)
async def reconfigure(request: Request, b64_config: str):
    config = decode_config(b64_config); api_key = config.get("stash_api_key", "")
    return templates.TemplateResponse("index.html", {"request": request, "api_key": api_key})

@app.get("/{b64_config}/manifest.json")
async def get_configured_manifest(b64_config: str):
    decode_config(b64_config)
    return Response(content=json.dumps(addon_manifest), media_type="application/json")

@app.get("/{b64_config}/catalog/{catalog_type}/{catalog_id_and_search:path}.json")
async def get_catalog(b64_config: str, catalog_type: str, catalog_id_and_search: str):
    config = decode_config(b64_config); api_key = config.get("stash_api_key")
    if not api_key: raise HTTPException(status_code=403, detail="API key is missing")
    search_query = None; catalog_id = catalog_id_and_search
    if "/search=" in catalog_id_and_search:
        parts = catalog_id_and_search.split("/search=")
        catalog_id = parts[0]
        search_query = unquote(parts[1]) if len(parts) > 1 else None
    metas = []
    async with aiohttp.ClientSession() as session:
        if search_query:
            if catalog_id == "stashdb_scenes":
                metas = await search_scenes(session, api_key, search_query)
            elif catalog_id == "stashdb_performers":
                metas = await search_performers(session, api_key, search_query)
        else:
            if catalog_id == "stashdb_scenes":
                metas = await get_scenes(session, api_key)
    return {"metas": metas}

@app.get("/{b64_config}/meta/{meta_type}/{meta_id}.json")
async def get_meta(b64_config: str, meta_type: str, meta_id: str):
    # CRITICAL FIX: Ignore requests for IDs that are not from our addon.
    if not meta_id.startswith("stashdb:"):
        return JSONResponse(content={"meta": {}}) # Return an empty meta object

    config = decode_config(b64_config)
    api_key = config.get("stash_api_key")
    if not api_key: raise HTTPException(status_code=403, detail="API key is missing")
    
    id_parts = meta_id.split(':')
    # We can now be sure id_parts has at least 3 elements because of the check above
    content_type, content_id = id_parts[1], id_parts[2]
    
    meta_data = None
    async with aiohttp.ClientSession() as session:
        if content_type == "scene":
            meta_data = await get_scene_meta(session, api_key, content_id)
        # Add performer meta logic here in the future
    
    if not meta_data:
        return JSONResponse(content={"meta": {}})
    
    return meta_data
