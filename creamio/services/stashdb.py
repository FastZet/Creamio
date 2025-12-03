import logging
from typing import Any, Dict, List, Optional

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from creamio.core.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class StashDBClient:
    """
    Async client for interacting with the StashDB GraphQL API.
    """

    def __init__(self, api_key: Optional[str] = None):
        # Use user-provided API key if available, otherwise fallback to server settings
        self.api_key = api_key or settings.STASHDB_API_KEY
        self.endpoint = settings.STASHDB_ENDPOINT
        
        # Prepare headers
        headers = {}
        if self.api_key:
            headers["ApiKey"] = self.api_key

        # Initialize GraphQL transport
        self.transport = AIOHTTPTransport(
            url=self.endpoint, 
            headers=headers
        )

    async def _execute_query(self, query_str: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper to execute a GraphQL query safely.
        """
        try:
            async with Client(transport=self.transport, fetch_schema_from_transport=False) as session:
                query = gql(query_str)
                return await session.execute(query, variable_values=variables)
        except Exception as e:
            logger.error(f"StashDB Query Failed: {e}")
            return {}

    async def search_scenes(self, search_term: str, page: int = 1) -> List[Dict[str, Any]]:
        """
        Search for scenes by keyword (fuzzy match).
        """
        query = """
        query SearchScenes($term: String!, $page: Int!) {
            findScenes(
                scene_filter: {
                    search: $term,
                    sort: DATE,
                    direction: DESC
                }
                filter: {
                    page: $page,
                    per_page: 20
                }
            ) {
                scenes {
                    id
                    title
                    details
                    date
                    release_date
                    duration
                    images {
                        url
                        width
                        height
                    }
                    studio {
                        name
                    }
                    performers {
                        name
                    }
                }
            }
        }
        """
        
        variables = {"term": search_term, "page": page}
        result = await self._execute_query(query, variables)
        
        # Safety check for empty results
        if not result or "findScenes" not in result:
            return []
            
        return result["findScenes"]["scenes"]

    async def get_scene(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific scene by ID.
        """
        query = """
        query GetScene($id: ID!) {
            findScene(id: $id) {
                id
                title
                details
                date
                release_date
                duration
                images {
                    url
                }
                studio {
                    name
                }
                performers {
                    name
                }
            }
        }
        """
        
        variables = {"id": scene_id}
        result = await self._execute_query(query, variables)
        
        return result.get("findScene")

    async def get_performer_scenes(self, performer_name: str, page: int = 1) -> List[Dict[str, Any]]:
        """
        Find a performer by name, then get their scenes.
        This is a two-step process in GraphQL logic usually, but StashDB 
        allows filtering scenes by performer_id if we find them.
        """
        # 1. Find the performer ID
        performer_query = """
        query FindPerformer($name: String!) {
            findPerformers(
                performer_filter: { search: $name }
                filter: { per_page: 1 }
            ) {
                performers {
                    id
                    name
                }
            }
        }
        """
        p_result = await self._execute_query(performer_query, {"name": performer_name})
        performers = p_result.get("findPerformers", {}).get("performers", [])
        
        if not performers:
            return []
            
        performer_id = performers[0]["id"]

        # 2. Find scenes for this performer
        scenes_query = """
        query PerformerScenes($pid: ID!, $page: Int!) {
            findScenes(
                scene_filter: {
                    performers: { value: [$pid], modifier: INCLUDES_ALL }
                    sort: DATE
                    direction: DESC
                }
                filter: {
                    page: $page,
                    per_page: 20
                }
            ) {
                scenes {
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
                }
            }
        }
        """
        
        variables = {"pid": performer_id, "page": page}
        result = await self._execute_query(scenes_query, variables)
        
        return result.get("findScenes", {}).get("scenes", [])
