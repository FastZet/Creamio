import aiohttp
import json

STASHDB_API_ENDPOINT = "https://stashdb.org/graphql"

async def get_scenes(session: aiohttp.ClientSession, api_key: str, skip: int = 0):
    # ... (this function remains the same, so I'm omitting it for brevity, 
    # but replace the whole file to be safe) ...
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


async def get_scene_meta(session: aiohttp.ClientSession, api_key: str, scene_id: str):
    """
    Fetches detailed metadata for a single scene from StashDB.
    """
    # CORRECTED QUERY: We now fetch performer -> name instead of just name.
    query = """
    query FindScene($id: ID!) {
      findScene(id: $id) {
        id
        title
        details
        date
        images {
          url
        }
        studio {
          name
        }
        tags {
          name
        }
        performers {
          performer {
            name
          }
        }
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
                if "errors" in data and data["errors"]:
                    print(f"StashDB API returned an error for scene {scene_id}: {json.dumps(data['errors'])}")
                    return None
                
                scene = data.get("data", {}).get("findScene")
                if not scene: return None

                poster = None
                images = scene.get('images')
                if images and len(images) > 0 and images[0]: poster = images[0].get('url')
                if not poster: poster = "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/logo-grey.png"
                
                director = scene.get('studio', {}).get('name')
                genres = [tag['name'] for tag in scene.get('tags', []) if tag and 'name' in tag]

                # CORRECTED CAST EXTRACTION: Go one level deeper to get the performer's name.
                cast = [
                    perf['performer']['name']
                    for perf in scene.get('performers', [])
                    if perf and perf.get('performer') and perf['performer'].get('name')
                ]

                meta = {
                    "id": f"stashdb:scene:{scene['id']}",
                    "type": "movie",
                    "name": scene.get('title') or 'No Title',
                    "poster": poster,
                    "background": poster,
                    "description": scene.get('details'),
                    "releaseInfo": scene.get('date', '')[:4] if scene.get('date') else '',
                    "director": [director] if director else [],
                    "cast": cast,
                    "genres": genres,
                }
                return {"meta": meta}
            else:
                response_text = await response.text()
                print(f"StashDB API Error for scene {scene_id}: {response.status} - Body: {response_text}")
                return None
    except Exception as e:
        print(f"An error occurred while fetching metadata for scene {scene_id}: {e}")
        return None
