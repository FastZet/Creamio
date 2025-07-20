from fastapi import FastAPI, Response, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import json
import base64

# Define the basic information for our addon
addon_manifest = {
    "id": "org.stremio.stashdb",
    "version": "1.0.1",
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
            "name": "StashDB Performers"
        }
    ],
    "logo": "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/favicon-32x32.png",
    "background": "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/stash-logo-horizontal-dark.png",
    # Add a new property to tell Stremio where the configuration page is
    "behaviorHints": {
        "configurable": True,
        "configurationRequired": True
    }
}

# Initialize FastAPI and the templating engine
app = FastAPI(
    title=addon_manifest["name"],
    version=addon_manifest["version"],
)
templates = Jinja2Templates(directory="templates")

# This endpoint serves our HTML configuration page
@app.get("/", response_class=HTMLResponse)
@app.get("/configure", response_class=HTMLResponse)
def configure(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# This is our new manifest endpoint that includes the user's config
@app.get("/{b64_config}/manifest.json")
def get_configured_manifest(b64_config: str):
    # Here you could decode and validate the config, but for now, we'll just serve the manifest
    return Response(content=json.dumps(addon_manifest), media_type="application/json")
