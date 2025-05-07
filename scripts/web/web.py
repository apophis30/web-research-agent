import re
import logging
import asyncio
from datetime import datetime
import nest_asyncio
from typing import Dict, List, Any


from scripts.web.newsAggregator import fetch_news
from scripts.web.analyzer import analyze_content, analyze_query
from scripts.web.webScraper import search_web, scrape_webpage

from config.redis import get_stream_data_from_redis, store_stream_data_in_redis
from config.llmClient import client

from dotenv import load_dotenv
load_dotenv() 


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Apply nest_asyncio to handle potential nested event loops
nest_asyncio.apply()
    

async def synthesize_information(user_id: str, sources: List[Dict[str, Any]], query: str):
    """
    Synthesize information from multiple sources to provide a coherent answer to the user's query.
    
    Args:
        user_id (str): User identifier for caching purposes.
        sources (List[Dict[str, Any]]): List of source dictionaries with content.
        query (str): The original user query.
        
    Returns:
        dict: Synthesized information and metadata.
    """
    # Generate a cache key based on sources hash and query
    import hashlib
    sources_hash = hashlib.md5(str(sorted(str(s.get('url', '')) for s in sources)).encode()).hexdigest()
    cache_key = f"{user_id}:synthesis:{sources_hash}:{hashlib.md5(query.encode()).hexdigest()}"
    
    # Check cache first
    cached_result = await get_stream_data_from_redis(cache_key)
    if cached_result:
        logger.info(f"Retrieved synthesis from cache for query: {query}")
        return cached_result
    
    # Prepare the context for synthesis by combining source contents
    context_parts = []
    for idx, source in enumerate(sources):
        content = source.get('content') or source.get('snippet') or source.get('summarized_content')
        if content:
            url = source.get('url', 'Unknown source')
            title = source.get('name') or source.get('title') or url
            context_parts.append(f"SOURCE {idx+1}: {title}\nURL: {url}\nCONTENT: {content[:2000]}")
    
    combined_context = "\n\n".join(context_parts)
    
    system_prompt = """
    You are an expert research assistant that synthesizes information from multiple sources 
    to provide comprehensive, accurate answers. Your task is to:
    
    1. Identify key information relevant to the query
    2. Resolve any contradictions between sources
    3. Organize information in a logical structure
    4. Generate a comprehensive answer that directly addresses the query
    5. Cite sources appropriately (Source 1, Source 2, etc.)
    
    Remember to prioritize accuracy and relevance while being concise.
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"QUERY: {query}\n\nSOURCES:\n{combined_context}"}
    ]
    
    try:
        response = await client.generate_data_with_llm(
            messages=messages,
            model="gpt-4o",  # Using a more powerful model for synthesis
            temperature=0.3
        )
        
        synthesis_text = response.choices[0].message.content
        
        # Extract any identified contradictions or missing information
        contradictions = re.search(r"contradictions:?\s*((?:.*?\n)+?)(?=\n\w+:|$)", synthesis_text, re.IGNORECASE | re.DOTALL)
        contradictions_text = contradictions.group(1).strip() if contradictions else None
        
        # Check if additional research is recommended
        research_suggestions = re.search(r"additional research:?\s*((?:.*?\n)+?)(?=\n\w+:|$)", synthesis_text, re.IGNORECASE | re.DOTALL)
        research_suggestions_text = research_suggestions.group(1).strip() if research_suggestions else None
        
        result = {
            "status": "success",
            "message": "Information synthesis completed",
            "synthesized_answer": synthesis_text,
            "metadata": {
                "query": query,
                "num_sources": len(sources),
                "source_urls": [s.get('url') for s in sources if s.get('url')],
                "contradictions": contradictions_text,
                "additional_research_suggestions": research_suggestions_text
            }
        }
        
        # Cache the result
        await store_stream_data_in_redis(cache_key, result)
        
        return result
    
    except Exception as e:
        logger.error(f"Error synthesizing information: {str(e)}")
        return {
            "status": "error",
            "message": f"Error synthesizing information: {str(e)}",
            "synthesized_answer": None,
            "metadata": None
        }

from math import log

def select_best_search_query(search_strategy, original_query_str):
    """
    Select the best search query using a BM25-inspired scoring approach.
    """
    # Extract search queries from search_strategy
    search_queries = re.findall(r'"([^"]+)"', search_strategy)
    
    if not search_queries:
        return original_query_str
    
    # If only one query, use it
    if len(search_queries) == 1:
        return search_queries[0]
    
    # Prepare the original query terms
    original_terms = original_query_str.lower().split()
    
    # BM25 parameters
    k1 = 1.2  # Term frequency saturation parameter
    b = 0.75  # Document length normalization parameter
    
    # Calculate average generated query length
    avg_query_length = sum(len(query.split()) for query in search_queries) / len(search_queries)
    
    scored_queries = []
    
    for query in search_queries:
        query_terms = query.lower().split()
        query_length = len(query_terms)
        
        # Initialize score
        bm25_score = 0
        
        # Base relevance features (outside of BM25)
        base_score = 0
        
        # Prefer queries with time indicators for recency
        time_indicators = ['latest', 'recent', 'current', 'today', 'updates', 'news']
        for indicator in time_indicators:
            if indicator.lower() in query.lower():
                base_score += 1
        
        # Prefer queries with quotes for exact phrases
        if '"' in query:
            base_score += 2
            
        # Calculate BM25-like score for term overlap with original query
        for term in original_terms:
            if term in query_terms:
                # Term frequency in generated query
                tf = query_terms.count(term)
                
                # Document length normalization component
                norm_factor = 1 - b + b * (query_length / avg_query_length)
                
                # BM25 formula (simplified - we're not using IDF since we're comparing against a single document)
                term_score = (tf * (k1 + 1)) / (tf + k1 * norm_factor)
                
                bm25_score += term_score
                
        # Combine BM25 score with base features
        final_score = bm25_score + base_score
        scored_queries.append((query, final_score))
    
    # Return the query with the highest score
    scored_queries.sort(key=lambda x: x[1], reverse=True)
    return scored_queries[0][0]

async def perform_research(user_id: str, query: str, depth: str = "standard"):
    """
    Main workflow function that orchestrates the entire research process.
    
    Args:
        user_id (str): User identifier for caching and tracking.
        query (str): The user's research query.
        depth (str): Research depth - "quick", "standard", or "deep".
        
    Returns:
        dict: Complete research results with synthesized answer and supporting data.
    """
    logger.info(f"Starting research for query: '{query}' with depth: {depth}")
    
    # Step 1: Analyze the query
    query_analysis = await analyze_query(user_id, query)
    if query_analysis.get("status") == "error":
        return {
            "status": "error",
            "message": f"Error analyzing query: {query_analysis.get('message')}",
            "result": None
        }
    
    # Extract search strategy for constructing better search query
    search_strategy = query_analysis["analysis"].get("search_strategy", "")
    original_query_str = query

    if search_strategy:
        query = select_best_search_query(search_strategy, original_query_str)
        print(f"\n🔍 Using search query from analysis: {query}")
    else:
        # Fallback to original query if no search strategy is available
        query = original_query_str


    intent = query_analysis["analysis"].get("intent", "")
    
    # Step 2: Determine if this is a news-related query
    NEWS_KEYWORDS = [
    "latest",
    "recent",
    "breaking",
    "news",
    "today",
    "this week",
    "this month",
    "current",
    "update",
    "live",
    "newest",
    "headline",
    "ongoing",
    str(datetime.now().year),
    ]
    is_news_query = any(term in intent.lower() for term in NEWS_KEYWORDS)
    
    # Step 3: Perform appropriate search based on query type and depth
    sources = []
    
    # For news queries or deep research, fetch recent news articles
    if is_news_query or depth == "deep":
        # Adjust days_back based on depth
        days_back = 3 if depth == "quick" else (7 if depth == "standard" else 30)
        
        logger.info(f"Fetching news for: {query} (days_back={days_back})")
        news_results = await fetch_news(user_id, query, days_back=days_back)
        
        if news_results.get("status") == "success":
            sources.extend([
                {
                    "name": article.get("title"),
                    "url": article.get("link"),
                    "snippet": article.get("title") + " - " + (article.get("source", "") or ""),  # Use title + source as snippet
                    "published_date": article.get("date"),
                    "source_type": "news"
                }
                for article in news_results.get("articles", [])
            ])
    
    # For all queries, perform web search
    search_results = await search_web(user_id, query)
    if search_results.get("contexts"):
        sources.extend([
            {
                "name": context.get("name"),
                "url": context.get("url"),
                "snippet": context.get("snippet"),
                "content": context.get("content"),
                "source_type": "web"
            }
            for context in search_results.get("contexts")
        ])
    
    # Step 4: For deep and standard research, scrape and analyze key sources
    if depth in ["deep", "standard"]:
        # Select top sources for deep scraping
        # For news sources, we don't need to scrape them since we already have the basic info
        web_sources = [s for s in sources if s["source_type"] == "web"]
        top_web_sources = web_sources[:3 if depth == "standard" else 5]
        
        results = []
        
        for source in top_web_sources:
            source_idx = sources.index(source)  # Get the index in the original sources list
            if source.get("url") and not source.get("content"):
                logger.info(f"Deep scraping source: {source.get('url')}")
                # Use asyncio.wait_for to enforce a global timeout on the entire scraping operation
            try:
                # Use a longer timeout for the entire operation (e.g., 60 seconds)
                scrape_result = await asyncio.wait_for(
                    scrape_webpage(user_id, source.get("url")),
                    timeout=60
                )
                
                # Log full result
                logger.info(f"🧪 Scrape result status for {source.get('url')}: {scrape_result.get('status')}")
                
                if scrape_result.get("status") == "success":
                    sources[source_idx]["summarized_content"] = scrape_result.get("summarized_content")
                    results.append({"url": source.get("url"), "success": True})
                else:
                    results.append({"url": source.get("url"), "success": False, "reason": scrape_result.get("message")})
            
            except asyncio.TimeoutError:
                logger.error(f"Global timeout reached for {source.get('url')}")
                results.append({"url": source.get("url"), "success": False, "reason": "Global timeout exceeded"})
            
            except Exception as e:
                logger.error(f"Unexpected error when processing {source.get('url')}: {str(e)}")
                results.append({"url": source.get("url"), "success": False, "reason": str(e)})

    
    # Step 5: Analyze content reliability and relevance for key sources
    if depth == "deep":
        # Prioritize a mix of news and web sources for analysis
        mixed_sources = sources[:5]  # Take top 5 sources regardless of type
        
        for idx, source in enumerate(mixed_sources):
            content = source.get("content") or source.get("summarized_content") or source.get("snippet")
            if content:
                logger.info(f"Analyzing content for source {idx+1}/5: {source.get('name')}")
                analysis_result = await analyze_content(user_id, content)
                if analysis_result.get("status") == "success":
                    source_idx = sources.index(source)  # Get the index in the original sources list
                    sources[source_idx]["analysis"] = analysis_result.get("analysis")
    
    # Step 6: Synthesize information from all sources
    if not sources:
        return {
            "status": "error",
            "message": "No relevant sources found for the query",
            "result": None
        }
    
    logger.info(f"Synthesizing information from {len(sources)} sources")
    synthesis_result = await synthesize_information(user_id, sources, query)
    
    # Step 7: Prepare and return final research result
    result = {
        "status": "success",
        "message": f"Research completed for query: {query}",
        "result": {
            "query": query,
            "query_analysis": query_analysis.get("analysis"),
            "answer": synthesis_result.get("synthesized_answer"),
            "sources": sources,
            "research_depth": depth,
            "timestamp": datetime.now().isoformat(),
            "additional_info": {
                "news_sources": sum(1 for s in sources if s.get("source_type") == "news"),
                "web_sources": sum(1 for s in sources if s.get("source_type") == "web"),
                "contradictions": synthesis_result.get("metadata", {}).get("contradictions"),
                "additional_research_suggestions": synthesis_result.get("metadata", {}).get("additional_research_suggestions")
            }
        }
    }
    
    return result
    

# Command-line interface for testing
async def main():
    """
    Main function for running the web research agent from the command line.
    """
    import argparse
    parser = argparse.ArgumentParser(description='Web Research Agent')
    parser.add_argument('query', help='Research query')
    parser.add_argument('--depth', choices=['quick', 'standard', 'deep'], default='standard', 
                        help='Research depth (default: standard)')
    parser.add_argument('--user-id', default='test_user', help='User ID for caching')
    
    args = parser.parse_args()
    
    print(f"Researching: '{args.query}' (Depth: {args.depth})")
    result = await perform_research(args.user_id, args.query, args.depth)
    
    if result.get("status") == "success":
        print("\n" + "="*80)
        print(f"ANSWER TO: {args.query}\n")
        print(result["result"]["answer"])
        print("\n" + "="*80)
        print(f"Sources: {len(result['result']['sources'])}")
        for idx, source in enumerate(result["result"]["sources"]):
            print(f"{idx+1}. {source.get('name')} - {source.get('url')}")
    else:
        print(f"Error: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(main())