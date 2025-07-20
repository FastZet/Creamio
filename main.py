from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse
import json

# Define the basic information for our addon
addon_manifest = {
    "id": "org.stremio.stashdb",
    "version": "1.0.0",
    "name": "StashDB Catalog",
    "description": "Provides an adult content catalog from StashDB.org for Stremio.",
    
    # We declare what this addon provides
    "resources": [
        "catalog",
        "meta"
    ],
    
    # The types of content this addon supports
    "types": ["movie", "series"], 
    
    # Information about the catalogs
    "catalogs": [
        {
            "type": "movie",
            "id": "stashdb_movies",
            "name": "StashDB Movies"
        },
        {
            "type": "series",
            "id": "stashdb_performers",
            "name": "StashDB Performers"
        }
    ],
    
    # A URL for the addon's logo
    "logo": "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/favicon-32x32.png",
    
    # A background image for the addon in Stremio
    "background": "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/stash-logo-horizontal-dark.png"
}

# Initialize the FastAPI app
app = FastAPI(
    title=addon_manifest["name"],
    version=addon_manifest["version"],
    description=addon_manifest["description"]
)

# Root endpoint that redirects to the manifest
@app.get("/")
def root():
    return RedirectResponse(url="/manifest.json")

# Manifest endpoint
@app.get("/manifest.json")
def get_manifest():
    return Response(content=json.dumps(addon_manifest), media_type="application/json")
