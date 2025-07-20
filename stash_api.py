import aiohttp
import json

# The public endpoint for the StashDB GraphQL API
STASHDB_API_ENDPOINT = "https://stashdb.org/graphql"

async def get_scenes(session: aiohttp.ClientSession, api_key: str, skip: int = 0):
    """
    Fetches the 100 most recent scenes from StashDB using the correct query.
    """
    # CORRECTED QUERY: The 'screenshot' field is directly on the Scene object, not under 'paths'.
    query = """
    query QueryScenes($input: SceneQueryInput!) {
      queryScenes(input: $input) {
        count
        scenes {
          id
          title
          date
          screenshot
        }
      }
    }
    """
    
    page = (skip // 100) + 1
    
    variables = {
        "input": {
            "sort": "date",
            "direction": "DESC",
            "page": page,
            "per_page": 100
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "ApiKey": api_key
    }
    payload = {
        "query": query,
        "variables": variables
    }

    try:
        async with session.post(STASHDB_API_ENDPOINT, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                scenes = data.get("data", {}).get("queryScenes", {}).get("scenes", [])
                
                stremio_metas = []
                for scene in scenes:
                    # CORRECTED POSTER EXTRACTION: Get 'screenshot' directly from the scene object.
                    poster = scene.get('screenshot')
                    if not poster:
                        poster = "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/logo-grey.png"

                    meta = {
                        "id": f"stashdb:scene:{scene['id']}",
                        "type": "movie",
                        "name": scene.get('title') or 'No Title',
                        "poster": poster
                    }
                    stremio_metas.append(meta)
                
                return stremio_metas
            else:
                response_text = await response.text()
                print(f"StashDB API Error: {response.status} - Body: {response_text}")
                return []
            
    except Exception as e:
        print(f"An error occurred while fetching from StashDB: {e}")
        return []
