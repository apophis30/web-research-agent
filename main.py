import uvicorn
from routers.app import app

if __name__ == "__main__":
    uvicorn.run(
        "routers.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
