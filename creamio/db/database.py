import time
import orjson
from databases import Database
from creamio.core.settings import get_settings

# Load settings to get the Database URL (sqlite+aiosqlite:///data/creamio.db)
settings = get_settings()

# Initialize the Database instance
database = Database(settings.DATABASE_URL)

async def init_db():
    """
    Initialize the database connection and create necessary tables.
    This is called when the addon starts.
    """
    await database.connect()
    
    # Create the search_cache table
    # key: The search query (e.g., "performer:12345" or "query:anal")
    # data: The JSON list of infohashes found
    # timestamp: When this was cached (for TTL expiry)
    query = """
    CREATE TABLE IF NOT EXISTS search_cache (
        key TEXT PRIMARY KEY,
        data TEXT NOT NULL,
        timestamp REAL NOT NULL
    )
    """
    await database.execute(query)


async def close_db():
    """
    Close the database connection.
    Called when the addon shuts down.
    """
    await database.disconnect()


async def get_cached_search(key: str) -> list | None:
    """
    Retrieve cached search results if they exist and are not expired.
    
    Args:
        key: The unique search key (e.g. 'stashdb:12345')
        
    Returns:
        List of results (dicts) or None if cache miss/expired
    """
    query = "SELECT data, timestamp FROM search_cache WHERE key = :key"
    row = await database.fetch_one(query, values={"key": key})
    
    if row:
        # Check if the cache entry has expired (TTL from settings)
        if time.time() - row["timestamp"] < settings.CACHE_TTL:
            # orjson loads bytes/str significantly faster than std json
            return orjson.loads(row["data"])
            
    return None


async def cache_search_results(key: str, results: list):
    """
    Save search results to the cache.
    
    Args:
        key: The unique search key
        results: The list of data to cache
    """
    # Serialize data to JSON string
    data_json = orjson.dumps(results).decode("utf-8")
    timestamp = time.time()
    
    # SQLite 'INSERT OR REPLACE' handles updating existing keys
    query = """
    INSERT OR REPLACE INTO search_cache (key, data, timestamp)
    VALUES (:key, :data, :timestamp)
    """
    await database.execute(query, values={
        "key": key,
        "data": data_json,
        "timestamp": timestamp
    })
