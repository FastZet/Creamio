import aiohttp
import json

# The public endpoint for the StashDB GraphQL API
STASHDB_API_ENDPOINT = "https://stashdb.org/graphql"

async def get_scenes(session: aiohttp.ClientSession, api_key: str, skip: int = 0):
    """
    Fetches the 100 most recent scenes from StashDB using aiohttp.
    """
    query = """
    query FindScenes($filter: FindFilter!, $scene_filter: SceneFilterInput!) {
      findScenes(filter: $filter, scene_filter: $scene_filter) {
        count
        scenes {
          id
          title
          date
          paths {
            screenshot
          }
        }
      }
    }
    """
    page = (skip // 100) + 1
    variables = {
        "filter": {"per_page": 100, "page": page, "sort": "date", "direction": "DESC"},
        "scene_filter": {}
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
                scenes = data.get("data", {}).get("findScenes", {}).get("scenes", [])
                
                stremio_metas = []
                for scene in scenes:
                    meta = {
                        "id": f"stashdb:scene:{scene['id']}",
                        "type": "movie",
                        "name": scene.get('title') or 'No Title',
                        "poster": scene.get('paths', {}).get('screenshot')
                    }
                    stremio_metas.append(meta)
                
                return stremio_metas
            else:
                print(f"StashDB API Error: {response.status}")
                return []
            
    except Exception as e:
        print(f"An error occurred while fetching from StashDB: {e}")
        return []
