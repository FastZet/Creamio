import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from creamio.core.settings import get_settings
from creamio.db.database import init_db, close_db
from creamio.api.routes import router

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager:
    - Connect to DB on startup
    - Disconnect on shutdown
    """
    logging.info("Starting Creamio Addon...")
    await init_db()
    yield
    logging.info("Shutting down Creamio Addon...")
    await close_db()

app = FastAPI(
    title="Creamio",
    description="Stremio Addon for StashDB & Debrid",
    version="1.0.0",
    lifespan=lifespan
)

# CORS (Allow requests from Stremio apps)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (if we add CSS/JS later)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API Routes
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=True
    )
