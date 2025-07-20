import aiohttp
import json

# The public endpoint for the StashDB GraphQL API
STASHDB_API_ENDPOINT = "https://stashdb.org/graphql"

async def get_scenes(session: aiohttp.ClientSession, api_key: str, skip: int = 0):
    """
    Fetches the 100 most recent scenes from StashDB using the correct query.
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
    
    # FINAL CORRECTION: Changed sort field from "date" to "created_at".
    variables = {
        "input": { "sort": "created_at", "direction": "DESC", "page": page, "per_page": 100 }
    }
    
    headers = { "Content-Type": "application/json", "ApiKey": api_key }
    payload = { "query": query, "variables": variables }

    try:
        async with session.post(STASHDB_API_ENDPOINT, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                
                if "errors" in data:
                    print(f"StashDB API returned an error: {json.dumps(data['errors'])}")
                    return []

                data_content = data.get("data")
                if not data_content or not isinstance(data_content, dict):
                    print("StashDB API Error: 'data' key is missing or not an object.")
                    return []

                query_scenes_data = data_content.get("queryScenes")
                if not query_scenes_data or not isinstance(query_scenes_data, dict):
                    print("StashDB API Error: 'queryScenes' key is missing or not an object.")
                    return []

                scenes = query_scenes_data.get("scenes")
                if scenes is None:
                    print("StashDB API Error: 'scenes' key is missing or null.")
                    return []
                
                stremio_metas = []
                for scene in scenes:
                    if not scene:
                        continue

                    poster = None
                    images = scene.get('images')
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
        print(f"An error occurred during the request to StashDB: {e}")
        return []
