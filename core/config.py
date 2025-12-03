from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Addon Info
    ADDON_ID: str = "community.creamio"
    ADDON_NAME: str = "Creamio"
    ADDON_VERSION: str = "0.1.0"
    
    # StashDB
    STASHDB_API_KEY: Optional[str] = None
    STASHDB_URL: str = "https://stashdb.org/graphql"
    
    # Debrid Providers
    REALDEBRID_API_KEY: Optional[str] = None
    TORBOX_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_PATH: str = "data/creamio.db"
    
    # Cache TTL (seconds)
    TORRENT_CACHE_TTL: int = 86400  # 1 day
    METADATA_CACHE_TTL: int = 604800  # 7 days
    
    # Scraper Settings
    SCRAPER_TIMEOUT: int = 30
    MAX_RESULTS_PER_SCRAPER: int = 50
    FUZZY_MATCH_THRESHOLD: int = 70  # 0-100, higher = stricter
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    def has_realdebrid(self) -> bool:
        return bool(self.REALDEBRID_API_KEY)
    
    def has_torbox(self) -> bool:
        return bool(self.TORBOX_API_KEY)
    
    def has_any_debrid(self) -> bool:
        return self.has_realdebrid() or self.has_torbox()
    
    def has_stashdb(self) -> bool:
        return bool(self.STASHDB_API_KEY)


settings = Settings()
