import os
import json
import logging
from redis import asyncio as aioredis
from typing import Dict, Any, Optional

# Initialize Redis client
redis_client = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def store_stream_data_in_redis(stream_id: str, data: Dict[str, Any], expiry: int = 3600) -> bool:
    """
    Store data in Redis with an expiry time.
    
    Args:
        stream_id (str): Unique identifier for the data
        data (Dict[str, Any]): Data to store
        expiry (int): Time in seconds before data expires
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        await redis_client.set(stream_id, json.dumps(data), ex=expiry)
        return True
    except Exception as e:
        logger.error(f"Redis storage error: {e}")
        return False

async def get_stream_data_from_redis(stream_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve data from Redis.
    
    Args:
        stream_id (str): Unique identifier for the data
        
    Returns:
        Optional[Dict[str, Any]]: The stored data or None if not found
    """
    try:
        data = await redis_client.get(stream_id)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Redis retrieval error: {e}")
        return None

async def delete_stream_data_from_redis(stream_id):
    await redis_client.delete(stream_id)


