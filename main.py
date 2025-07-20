from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json
import base64
import aiohttp  # Import the new library

# Import the function we created in our new file
from stash_api import get_scenes

# --- (The addon_manifest dictionary remains the same as before) ---
addon_manifest = {
    "id": "org.stremio.stashdb",
    "version": "1.0.2",
    "name": "StashDB Catalog",
    "description": "Provides an adult content catalog from StashDB.org for Stremio.",
    "resources": ["catalog", "meta"],
    "types": ["movie", "series"], 
    "catalogs": [
        {
            "type": "movie",
            "id": "stashdb_scenes",
            "name": "StashDB Scenes"
        },
        {
            "type": "series",
            "id": "stashdb_performers",
            "name": "StashDB Performers (Coming Soon)"
        }
    ],
    "logo": "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/favicon-32x32.png",
    "background": "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/stash-logo-horizontal-dark.png",
    "behaviorHints": {
        "configurable": True,
        "configurationRequired": True
    }
}


app = FastAPI(
    title=addon_manifest["name"],
    version=addon_manifest["version"],
)
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

# This endpoint is now an 'async' function
@app.get("/{b64_config}/catalog/{catalog_type}/{catalog_id}.json")
async def get_catalog(b64_config: str, catalog_type: str, catalog_id: str):
    config = decode_config(b64_config)
    api_key = config.get("stash_api_key")

    if not api_key:
        raise HTTPException(status_code=403, detail="API key is missing from configuration")

    metas = []
    # We create an aiohttp session to make the request
    async with aiohttp.ClientSession() as session:
        if catalog_id == "stashdb_scenes":
            # We now 'await' the result of our async function
            metas = await get_scenes(session, api_key)
        elif catalog_id == "stashdb_performers":
            pass

    return {"metas": metas}
