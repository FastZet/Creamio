from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json
import base64

# Import the function we created in our new file
from stash_api import get_scenes

# Define the basic information for our addon
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
    """Decodes the base64 config string and returns a dictionary."""
    try:
        decoded_bytes = base64.b64decode(b64_config)
        return json.loads(decoded_bytes.decode('utf-8'))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid configuration format")

# --- Endpoints ---

@app.get("/", response_class=HTMLResponse)
@app.get("/configure", response_class=HTMLResponse)
def configure(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/{b64_config}/manifest.json")
def get_configured_manifest(b64_config: str):
    # This just confirms the config is valid before serving the manifest
    decode_config(b64_config)
    return Response(content=json.dumps(addon_manifest), media_type="application/json")

@app.get("/{b64_config}/catalog/{catalog_type}/{catalog_id}.json")
def get_catalog(b64_config: str, catalog_type: str, catalog_id: str):
    config = decode_config(b64_config)
    api_key = config.get("stash_api_key")

    if not api_key:
        raise HTTPException(status_code=403, detail="API key is missing from configuration")

    metas = []
    if catalog_id == "stashdb_scenes":
        metas = get_scenes(api_key)
    # We will add logic for performers later
    elif catalog_id == "stashdb_performers":
        # Placeholder
        pass

    return {"metas": metas}
