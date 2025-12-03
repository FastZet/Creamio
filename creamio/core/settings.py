import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application Settings
    
    These settings are loaded from environment variables or a .env file.
    They control the server-side behavior of the Creamio addon.
    """

    # --- Server Configuration ---
    # The host to bind the server to (0.0.0.0 for Docker/Production)
    HOST: str = "0.0.0.0"
    
    # The port to run the server on
    PORT: int = 8000
    
    # Logging level (DEBUG, INFO, WARNING, ERROR)
    LOG_LEVEL: str = "INFO"
    
    # --- StashDB Configuration ---
    # The GraphQL endpoint for StashDB (Defaults to the public instance)
    STASHDB_ENDPOINT: str = "https://stashdb.org/graphql"
    
    # Server-side StashDB API Key. 
    # If provided here, it can be used as a fallback if the user doesn't provide one.
    STASHDB_API_KEY: str | None = None

    # --- Database & Caching ---
    # Location of the SQLite database for caching torrent results
    # We use a local file by default, stored in a 'data' directory
    DATABASE_URL: str = "sqlite+aiosqlite:///data/creamio.db"
    
    # How long to cache scraper results (in seconds)
    # Default: 24 hours (86400 seconds)
    CACHE_TTL: int = 86400
    
    # --- Scraper Configuration ---
    # User Agent to use when scraping torrent sites to avoid blocking
    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    )

    # Proxy URL for scraping (Optional)
    # Useful if torrent sites are blocked in your server's region
    SCRAPE_PROXY: str | None = None

    # --- Pydantic Configuration ---
    # This tells Pydantic to read from a .env file if present
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra variables in .env
    )


@lru_cache
def get_settings() -> Settings:
    """
    Factory function to get the settings instance.
    Uses lru_cache to ensure we only load the environment variables once.
    """
    return Settings()

# Create the data directory if it doesn't exist
# This ensures our SQLite database has a place to live
data_dir = Path("data")
if not data_dir.exists():
    data_dir.mkdir(parents=True, exist_ok=True)
