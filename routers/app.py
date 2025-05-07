from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
import os
import uuid
import sys
import signal
import psutil
import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Import the research functions from your existing code
from scripts.web.web import (
    perform_research,
)

from scripts.web.newsAggregator import (
    fetch_news
)

from scripts.web.webScraper import (
    search_web,
    scrape_webpage
)

# Define signal handler function
def setup_signal_handlers():
    """
    Setup signal handlers to gracefully terminate the application
    and all browser processes.
    """
    def signal_handler(sig, frame):
        print(f"\nReceived signal {sig}. Cleaning up...")
        
        # Kill all chromium/chrome processes
        try:
            process = psutil.Process(os.getpid())
            for child in process.children(recursive=True):
                if "chromium" in child.name().lower() or "chrome" in child.name().lower():
                    print(f"Terminating browser process: {child.pid}")
                    child.terminate()
            
            # Force kill after a short timeout
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(asyncio.sleep(0.5))
            else:
                try:
                    loop.run_until_complete(asyncio.sleep(0.5))
                except RuntimeError:
                    # If the event loop is closed
                    pass
                
            for child in process.children(recursive=True):
                if child.is_running() and ("chromium" in child.name().lower() or "chrome" in child.name().lower()):
                    print(f"Force killing browser process: {child.pid}")
                    child.kill()
        except Exception as e:
            print(f"Error cleaning up browser processes: {e}")
            
        print("Exiting...")
        sys.exit(0)
    
    # Register the signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if hasattr(signal, 'SIGHUP'):  # Not available on Windows
        signal.signal(signal.SIGHUP, signal_handler)

# Call setup_signal_handlers early
setup_signal_handlers()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application starting up")
    yield
    # Shutdown
    logger.info("Application shutting down, cleaning up resources...")
    try:
        # Kill any remaining chromium processes
        process = psutil.Process(os.getpid())
        for child in process.children(recursive=True):
            if "chromium" in child.name().lower() or "chrome" in child.name().lower():
                logger.info(f"Terminating browser process on shutdown: {child.pid}")
                child.terminate()
    except Exception as e:
        logger.error(f"Error during shutdown cleanup: {str(e)}")

app = FastAPI(
    title="Web Research API", 
    description="API for web search and research capabilities", 
    lifespan=lifespan
)

# Add CORS middleware to allow requests from your Streamlit app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    query: str
    depth: str = "standard" 
    user_id: Optional[str] = None

class WebSearchRequest(BaseModel):
    query: str
    user_id: Optional[str] = None

class WebpageRequest(BaseModel):
    url: str
    user_id: Optional[str] = None
    selector_query: Optional[str] = None
    timeout: Optional[int] = 10

@app.get("/")
async def root():
    return {"message": "Welcome to the Web Research API"}

@app.post("/research")
async def research(request: ResearchRequest):
    """
    Perform comprehensive research on the given query with specified depth.
    """
    # Generate a user ID if not provided
    user_id = request.user_id or f"anonymous_{uuid.uuid4().hex[:8]}"
    
    try:
        result = await perform_research(user_id, request.query, request.depth)
        return result
    except Exception as e:
        logger.error(f"Research failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")

@app.post("/search")
async def search(request: WebSearchRequest):
    """
    Perform a basic web search on the given query.
    """
    user_id = request.user_id or f"anonymous_{uuid.uuid4().hex[:8]}"
    
    try:
        result = await search_web(user_id, request.query)
        return result
    except Exception as e:
        logger.error(f"Web search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Web search failed: {str(e)}")

@app.post("/scrape")
async def scrape(request: WebpageRequest):
    """
    Scrape and summarize content from a webpage.
    """
    user_id = request.user_id or f"anonymous_{uuid.uuid4().hex[:8]}"
    
    try:
        # Add a global timeout to the scrape operation
        result = await asyncio.wait_for(
            scrape_webpage(
                user_id, 
                request.url, 
                timeout=request.timeout or 10,
                selector_query=request.selector_query or ""
            ),
            timeout=60  # 60 second global timeout
        )
        return result
    except asyncio.TimeoutError:
        logger.error(f"Global timeout reached for {request.url}")
        raise HTTPException(status_code=504, detail=f"Webpage scraping timed out after 60 seconds")
    except Exception as e:
        logger.error(f"Webpage scraping failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webpage scraping failed: {str(e)}")

@app.post("/news")
async def news(request: WebSearchRequest, days_back: int = Query(7, ge=1, le=30)):
    """
    Fetch recent news articles related to the query.
    """
    user_id = request.user_id or f"anonymous_{uuid.uuid4().hex[:8]}"
    
    try:
        result = await fetch_news(user_id, request.query, days_back=days_back)
        return result
    except Exception as e:
        logger.error(f"News fetching failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"News fetching failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Make sure psutil is installed
    try:
        import psutil
    except ImportError:
        print("psutil not found. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        print("psutil installed successfully")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)