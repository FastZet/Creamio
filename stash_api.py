import aiohttp
import json

STASHDB_API_ENDPOINT = "https://stashdb.org/graphql"

async def get_scenes(session: aiohttp.ClientSession, api_key: str, skip: int = 0):
    # This function remains the same as before
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
    variables = { "input": { "sort": "DATE", "direction": "DESC", "page": page, "per_page": 100 } }
    headers = { "Content-Type": "application/json", "ApiKey": api_key }
    payload = { "query": query, "variables": variables }
    try:
        async with session.post(STASHDB_API_ENDPOINT, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                if "errors" in data and data["errors"]: return []
                scenes = data.get("data", {}).get("queryScenes", {}).get("scenes", [])
                if scenes is None: return []
                stremio_metas = []
                for scene in scenes:
                    if not scene: continue
                    poster = None
                    images = scene.get('images')
                    if images and len(images) > 0 and images[0]: poster = images[0].get('url')
                    if not poster: poster = "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/logo-grey.png"
                    meta = { "id": f"stashdb:scene:{scene['id']}", "type": "movie", "name": scene.get('title') or 'No Title', "poster": poster }
                    stremio_metas.append(meta)
                return stremio_metas
            else:
                print(f"StashDB API Error: {response.status} - Body: {await response.text()}")
                return []
    except Exception as e:
        print(f"An error occurred while fetching scenes: {e}")
        return []

# --- NEW FUNCTION FOR SEARCHING ---
async def search_scenes(session: aiohttp.ClientSession, api_key: str, search_query: str):
    """
    Searches for scenes on StashDB based on a query string.
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
    # The 'q' property in the filter is used for free-text search
    variables = { "input": { "q": search_query, "per_page": 100 } }
    headers = { "Content-Type": "application/json", "ApiKey": api_key }
    payload = { "query": query, "variables": variables }
    try:
        async with session.post(STASHDB_API_ENDPOINT, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                if "errors" in data and data["errors"]:
                    print(f"StashDB Search API returned an error: {json.dumps(data['errors'])}")
                    return []
                scenes = data.get("data", {}).get("queryScenes", {}).get("scenes", [])
                if scenes is None: return []
                
                stremio_metas = []
                for scene in scenes:
                    if not scene: continue
                    poster = None
                    images = scene.get('images')
                    if images and len(images) > 0 and images[0]: poster = images[0].get('url')
                    if not poster: poster = "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/logo-grey.png"
                    meta = { "id": f"stashdb:scene:{scene['id']}", "type": "movie", "name": scene.get('title') or 'No Title', "poster": poster }
                    stremio_metas.append(meta)
                return stremio_metas
            else:
                print(f"StashDB API Error: {response.status} - Body: {await response.text()}")
                return []
    except Exception as e:
        print(f"An error occurred while searching scenes: {e}")
        return []

async def get_scene_meta(session: aiohttp.ClientSession, api_key: str, scene_id: str):
    # This function also remains the same
    query = """
    query FindScene($id: ID!) {
      findScene(id: $id) {
        id, title, details, date, images { url },
        studio { name }, tags { name },
        performers { performer { name } }
      }
    }
    """
    variables = { "id": scene_id }
    headers = { "Content-Type": "application/json", "ApiKey": api_key }
    payload = { "query": query, "variables": variables }
    try:
        async with session.post(STASHDB_API_ENDPOINT, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                if "errors" in data and data["errors"]: return None
                scene = data.get("data", {}).get("findScene")
                if not scene: return None
                poster = None
                images = scene.get('images')
                if images and len(images) > 0 and images[0]: poster = images[0].get('url')
                if not poster: poster = "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/logo-grey.png"
                director = scene.get('studio', {}).get('name')
                genres = [tag['name'] for tag in scene.get('tags', []) if tag and 'name' in tag]
                cast = [perf['performer']['name'] for perf in scene.get('performers', []) if perf and perf.get('performer') and perf['performer'].get('name')]
                meta = { "id": f"stashdb:scene:{scene['id']}", "type": "movie", "name": scene.get('title') or 'No Title', "poster": poster, "background": poster, "description": scene.get('details'), "releaseInfo": scene.get('date', '')[:4] if scene.get('date') else '', "director": [director] if director else [], "cast": cast, "genres": genres, }
                return {"meta": meta}
            else:
                print(f"StashDB API Error for scene {scene_id}: {response.status} - Body: {await response.text()}")
                return None
    except Exception as e:
        print(f"An error occurred while fetching metadata for scene {scene_id}: {e}")
        return None
