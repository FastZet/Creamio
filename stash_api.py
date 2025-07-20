import aiohttp
import json

# The public endpoint for the StashDB GraphQL API
STASHDB_API_ENDPOINT = "https://stashdb.org/graphql"

async def get_scenes(session: aiohttp.ClientSession, api_key: str, skip: int = 0):
    """
    Fetches the 100 most recent scenes from StashDB with robust error handling.
    """
    query = """
    query QueryScenes($input: SceneQueryInput!) {
      queryScenes(input: $input) {
        count
        scenes {
          id
          title
          date
          images {
            url
          }
        }
      }
    }
    """
    
    page = (skip // 100) + 1
    variables = {
        "input": { "sort": "date", "direction": "DESC", "page": page, "per_page": 100 }
    }
    headers = { "Content-Type": "application/json", "ApiKey": api_key }
    payload = { "query": query, "variables": variables }

    try:
        async with session.post(STASHDB_API_ENDPOINT, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                scenes = data.get("data", {}).get("queryScenes", {}).get("scenes", [])
                
                if not scenes: # Handle case where scenes list is empty or None
                    return []

                stremio_metas = []
                for scene in scenes:
                    # ADDED CHECK: Ensure the scene object itself is not None before processing.
                    if not scene:
                        continue

                    poster = None
                    images = scene.get('images')
                    
                    # ADDED CHECK: Ensure images list is not empty and its first item is not None.
                    if images and len(images) > 0 and images[0]:
                        poster = images[0].get('url')
                    
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
        # This is the block that was triggered.
        print(f"An error occurred while fetching from StashDB: {e}")
        return []
