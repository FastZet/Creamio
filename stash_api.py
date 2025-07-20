import grequests
import json

# The public endpoint for the StashDB GraphQL API
STASHDB_API_ENDPOINT = "https://stashdb.org/graphql"

def get_scenes(api_key, skip=0):
    """
    Fetches the 100 most recent scenes from StashDB.
    """
    # This is the GraphQL query we will send to StashDB.
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

    # These are the variables for the query. We sort by date descending.
    # We use 'per_page' for pagination. StashDB's pagination is page-based.
    # 'skip' will be used to calculate the page number.
    page = (skip // 100) + 1
    variables = {
        "filter": {"per_page": 100, "page": page, "sort": "date", "direction": "DESC"},
        "scene_filter": {}
    }

    # We need to send the API key in the headers.
    headers = {
        "Content-Type": "application/json",
        "ApiKey": api_key
    }

    # The request payload for a GraphQL query
    payload = {
        "query": query,
        "variables": variables
    }

    try:
        # We use grequests for making the HTTP request.
        # It's a simple library for async requests.
        response = grequests.map([
            grequests.post(STASHDB_API_ENDPOINT, headers=headers, data=json.dumps(payload))
        ])[0]

        if response and response.status_code == 200:
            scenes = response.json().get("data", {}).get("findScenes", {}).get("scenes", [])
            
            # Now we transform the scene data into the format Stremio expects
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
            print(f"StashDB API Error: {response.status_code if response else 'No response'}")
            return []
            
    except Exception as e:
        print(f"An error occurred while fetching from StashDB: {e}")
        return []
