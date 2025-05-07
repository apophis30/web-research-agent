import os
import logging
import re
from datetime import datetime, timedelta
from urllib.parse import quote
from dotenv import load_dotenv
from serpapi import GoogleSearch
from config.redis import get_stream_data_from_redis, store_stream_data_in_redis

# Get .env variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_query(query: str) -> str:
    """
    Parse and sanitize a search query.
    
    Args:
        query (str): The raw search query.
        
    Returns:
        str: The sanitized query ready for search.
    """
    if not query or not query.strip():
        return "news"  # Default query if empty
    
    # Remove any potentially harmful characters
    query = re.sub(r'[^\w\s\-\+\'\"]+', ' ', query)
    
    # Trim and remove extra whitespace
    query = ' '.join(query.strip().split())
    
    # URL encode the query
    query = quote(query)
    
    return query

async def fetch_news(user_id: str, query: str, max_results: int = 20, days_back: int = 7):
    """
    Fetch recent news articles related to a specific query.
    
    Args:
        user_id (str): User identifier for caching purposes.
        query (str): The search query for news.
        max_results (int): Maximum number of news articles to return.
        days_back (int): Maximum age of news articles in days.
        
    Returns:
        dict: A dictionary containing news articles and metadata.
    """
    # Sanitize and parse the query
    parsed_query = parse_query(query)
    
    # Use raw query for cache key to avoid regenerating for equivalent queries
    cache_key = f"{user_id}:news:{query}:{max_results}:{days_back}"
    
    # Check cache first
    cached_result = await get_stream_data_from_redis(cache_key)
    if cached_result:
        logger.info(f"Retrieved news results from cache for query: {query}")
        return cached_result
    
    # Set up SerpAPI parameters
    params = {
        "engine": "google_news",
        "q": parsed_query,
        "gl": "in",
        "hl": "en",
        "api_key": os.getenv("SERP_API_KEY")
    }
    
    # Validate parameters
    if not params["api_key"]:
        logger.error("Missing SERP_API_KEY environment variable")
        return {
            "status": "error",
            "message": "API key is missing. Please check your environment configuration.",
            "articles": [],
            "metadata": {
                "query": query,
                "parsed_query": parsed_query,
                "max_results": max_results,
                "days_back": days_back
            }
        }
    
    try:
        # Execute search
        logger.info(f"Fetching news for query: {query}")
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Check if we have valid results
        if "news_results" not in results or not results["news_results"]:
            logger.warning(f"No news results found for query: {query}")
            return {
                "status": "error",
                "message": f"No news results found for query: {query}",
                "articles": [],
                "metadata": {
                    "query": query,
                    "parsed_query": parsed_query,
                    "max_results": max_results,
                    "days_back": days_back
                }
            }
        
        # Extract news articles from search results
        news_articles = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for article in results["news_results"]:
            # Skip if we've reached our maximum
            if len(news_articles) >= max_results:
                break
                
            # Try to parse the date
            article_date = None
            try:
                if "date" in article:
                    # Parse date format like "11/12/2024, 09:03 AM, +0200 EET"
                    date_str = article["date"].split(",")[0] + "," + article["date"].split(",")[1]
                    article_date = datetime.strptime(date_str, "%m/%d/%Y, %I:%M %p")
                    
                    # Skip articles older than days_back
                    if article_date < cutoff_date:
                        continue
            except Exception as e:
                logger.warning(f"Could not parse date for article: {article.get('title', 'Unknown')}, error: {e}")
            
            # Clean and extract article data
            cleaned_article = {
                "position": article.get("position"),
                "title": article.get("title"),
                "link": article.get("link"),
                "date": article.get("date"),
                "thumbnail": article.get("thumbnail"),
                "source": article.get("source", {}).get("name"),
            }
            
            # Add authors if available
            if "source" in article and "authors" in article["source"]:
                cleaned_article["authors"] = article["source"]["authors"]
            
            news_articles.append(cleaned_article)
        
        # Prepare the response
        result = {
            "status": "success",
            "message": f"Successfully retrieved news for query: {query}",
            "articles": news_articles,
            "metadata": {
                "query": query,
                "parsed_query": parsed_query,
                "max_results": max_results,
                "days_back": days_back,
                "total_results_available": len(results["news_results"]),
                "total_results_returned": len(news_articles)
            }
        }
        
        # Cache the result
        await store_stream_data_in_redis(cache_key, result)
        
        return result
        
    except Exception as e:
        error_message = f"Error fetching news for query '{query}': {str(e)}"
        logger.error(error_message)
        return {
            "status": "error",
            "message": error_message,
            "articles": [],
            "metadata": {
                "query": query,
                "max_results": max_results,
                "days_back": days_back
            }
        }