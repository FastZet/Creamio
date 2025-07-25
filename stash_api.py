import aiohttp
import json

STASHDB_API_ENDPOINT = "https://stashdb.org/graphql"

async def get_scenes(session: aiohttp.ClientSession, api_key: str, skip: int = 0):
    query = """
    query QueryScenes($input: SceneQueryInput!) {
      queryScenes(input: $input) {
        count, scenes { id, title, date, images { url } }
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
                    poster = None; images = scene.get('images')
                    if images and len(images) > 0 and images[0]: poster = images[0].get('url')
                    if not poster: poster = "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/logo-grey.png"
                    meta = { "id": f"stashdb:scene:{scene['id']}", "type": "movie", "name": scene.get('title') or 'No Title', "poster": poster }
                    stremio_metas.append(meta)
                return stremio_metas
            else: return []
    except Exception as e:
        print(f"An error occurred while fetching scenes: {e}"); return []

async def search_scenes(session: aiohttp.ClientSession, api_key: str, search_query: str):
    # CORRECTED QUERY: The argument is 'scene_filter' of type 'SceneFilterInput'
    query = """
    query QueryScenes($scene_filter: SceneFilterInput!) {
      queryScenes(scene_filter: $scene_filter, filter: {per_page: 100}) {
        count, scenes { id, title, date, images { url } }
      }
    }
    """
    # CORRECTED VARIABLES: The variables object matches the query arguments.
    variables = { "scene_filter": { "q": search_query } }
    headers = { "Content-Type": "application/json", "ApiKey": api_key }
    payload = { "query": query, "variables": variables }
    try:
        async with session.post(STASHDB_API_ENDPOINT, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                if "errors" in data and data["errors"]:
                    print(f"StashDB Scene Search API returned an error: {json.dumps(data['errors'])}")
                    return []
                scenes = data.get("data", {}).get("queryScenes", {}).get("scenes", [])
                if scenes is None: return []
                stremio_metas = []
                for scene in scenes:
                    if not scene: continue
                    poster = None; images = scene.get('images')
                    if images and len(images) > 0 and images[0]: poster = images[0].get('url')
                    if not poster: poster = "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/logo-grey.png"
                    meta = { "id": f"stashdb:scene:{scene['id']}", "type": "movie", "name": scene.get('title') or 'No Title', "poster": poster }
                    stremio_metas.append(meta)
                return stremio_metas
            else: return []
    except Exception as e:
        print(f"An error occurred while searching scenes: {e}"); return []

async def search_performers(session: aiohttp.ClientSession, api_key: str, search_query: str):
    # CORRECTED QUERY: The argument is 'performer_filter' of type 'PerformerFilterInput'
    query = """
    query QueryPerformers($performer_filter: PerformerFilterInput!) {
      queryPerformers(performer_filter: $performer_filter, filter: {per_page: 100}) {
        count, performers { id, name, images { url } }
      }
    }
    """
    # CORRECTED VARIABLES: The variables object matches the query arguments.
    variables = { "performer_filter": { "q": search_query } }
    headers = { "Content-Type": "application/json", "ApiKey": api_key }
    payload = { "query": query, "variables": variables }
    try:
        async with session.post(STASHDB_API_ENDPOINT, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                if "errors" in data and data["errors"]:
                    print(f"StashDB Performer Search API returned an error: {json.dumps(data['errors'])}")
                    return []
                performers = data.get("data", {}).get("queryPerformers", {}).get("performers", [])
                if performers is None: return []
                stremio_metas = []
                for performer in performers:
                    if not performer: continue
                    poster = None; images = performer.get('images')
                    if images and len(images) > 0 and images[0]: poster = images[0].get('url')
                    if not poster: poster = "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/logo-grey.png"
                    meta = { "id": f"stashdb:performer:{performer['id']}", "type": "series", "name": performer.get('name') or 'No Name', "poster": poster }
                    stremio_metas.append(meta)
                return stremio_metas
            else: return []
    except Exception as e:
        print(f"An error occurred while searching performers: {e}"); return []

async def get_scene_meta(session: aiohttp.ClientSession, api_key: str, scene_id: str):
    # This function is correct and remains unchanged.
    query = """
    query FindScene($id: ID!) {
      findScene(id: $id) {
        id, title, details, date, images { url },
        studio { name }, tags { name },
        performers { performer { name } }
      }
    }
    """
    variables = { "id": scene_id }; headers = { "Content-Type": "application/json", "ApiKey": api_key }
    payload = { "query": query, "variables": variables }
    try:
        async with session.post(STASHDB_API_ENDPOINT, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                if "errors" in data and data["errors"]: return None
                scene = data.get("data", {}).get("findScene")
                if not scene: return None
                poster = None; images = scene.get('images')
                if images and len(images) > 0 and images[0]: poster = images[0].get('url')
                if not poster: poster = "https://raw.githubusercontent.com/stashapp/stash/develop/ui/v2.0/src/assets/images/logo-grey.png"
                director = scene.get('studio', {}).get('name'); genres = [tag['name'] for tag in scene.get('tags', []) if tag and 'name' in tag]
                cast = [perf['performer']['name'] for perf in scene.get('performers', []) if perf and perf.get('performer') and perf['performer'].get('name')]
                meta = { "id": f"stashdb:scene:{scene['id']}", "type": "movie", "name": scene.get('title') or 'No Title', "poster": poster, "background": poster, "description": scene.get('details'), "releaseInfo": scene.get('date', '')[:4] if scene.get('date') else '', "director": [director] if director else [], "cast": cast, "genres": genres, }
                return {"meta": meta}
            else: return None
    except Exception as e:
        print(f"An error occurred while fetching metadata for scene {scene_id}: {e}"); return None
