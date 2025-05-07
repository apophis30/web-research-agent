import logging
import json
import re
from typing import Optional, Dict, Any

from config.llmClient import client
from config.redis import get_stream_data_from_redis, store_stream_data_in_redis

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def analyze_content(user_id: str, content: str, criteria: Optional[Dict[str, Any]] = None):
    """
    Analyze content for relevance, reliability, and other specified criteria.
    
    Args:
        user_id (str): User identifier for caching purposes.
        content (str): The content to analyze.
        criteria (Dict[str, Any], optional): Specific criteria to evaluate.
        
    Returns:
        dict: Analysis results with scores and explanations.
    """
    if not criteria:
        criteria = {
            "relevance": True,
            "reliability": True,
            "bias": True,
            "factuality": True,
            "recency": True
        }
    
    # Generate a cache key based on content hash and criteria
    import hashlib
    content_hash = hashlib.md5(content.encode()).hexdigest()
    criteria_str = json.dumps(criteria, sort_keys=True)
    cache_key = f"{user_id}:analysis:{content_hash}:{hashlib.md5(criteria_str.encode()).hexdigest()}"
    
    # Check cache first
    cached_result = await get_stream_data_from_redis(cache_key)
    if cached_result:
        logger.info(f"Retrieved content analysis from cache")
        return cached_result
    
    # Prepare prompt for LLM-based analysis
    system_prompt = """
    You are a content analyzer that evaluates text based on specified criteria. 
    For each criterion, provide a score from 0-10 and a brief explanation.
    """
    
    criteria_descriptions = {
        "relevance": "How relevant the content is to typical research queries",
        "reliability": "How reliable and trustworthy the information appears to be",
        "bias": "The degree of bias present in the content (lower score means more biased)",
        "factuality": "How factual vs. opinion-based the content is",
        "recency": "How recent or current the information appears to be"
    }
    
    # Build criteria prompt
    criteria_prompt = ""
    for criterion, enabled in criteria.items():
        if enabled and criterion in criteria_descriptions:
            criteria_prompt += f"- {criterion}: {criteria_descriptions[criterion]}\n"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analyze the following content based on these criteria:\n{criteria_prompt}\n\nContent: {content[:4000]}"}
    ]
    
    try:
        response = await client.generate_data_with_llm(
            messages=messages,
            model="gpt-4o-mini",
            temperature=0.2
        )
        
        analysis_text = response.choices[0].message.content
        
        # Parse the response to extract scores and explanations
        analysis_results = {}
        for criterion in criteria:
            if criteria.get(criterion):
                pattern = rf"{criterion}\s*(?::|score:?)\s*(\d+(?:\.\d+)?)/10(.*?)(?=\n\n|\n[A-Za-z]+\s*(?::|score:?)|$)"
                match = re.search(pattern, analysis_text, re.IGNORECASE | re.DOTALL)
                if match:
                    score = float(match.group(1))
                    explanation = match.group(2).strip()
                    analysis_results[criterion] = {
                        "score": score,
                        "explanation": explanation
                    }
                else:
                    analysis_results[criterion] = {
                        "score": None,
                        "explanation": "Could not extract score and explanation from analysis."
                    }
        
        result = {
            "status": "success",
            "message": "Content analysis completed",
            "analysis": analysis_results,
            "overall_analysis": analysis_text
        }
        
        # Cache the result
        await store_stream_data_in_redis(cache_key, result)
        
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing content: {str(e)}")
        return {
            "status": "error",
            "message": f"Error analyzing content: {str(e)}",
            "analysis": None,
            "overall_analysis": None
        }
    

async def analyze_query(user_id: str, query: str):
    """
    Analyze a user's research query to determine intent, components, and search strategy.
    
    Args:
        user_id (str): User identifier for caching purposes.
        query (str): The user's research query.
        
    Returns:
        dict: Analysis of the query with intent, components, and search strategy.
    """
    cache_key = f"{user_id}:query_analysis:{query}"
    
    # Check cache first
    cached_result = await get_stream_data_from_redis(cache_key)
    if cached_result:
        logger.info(f"Retrieved query analysis from cache for query: {query}")
        return cached_result
    
    system_prompt = """
    You are a query analysis expert. When provided with a research query, analyze it to determine:
    1. The primary intent (factual information, opinion/analysis, recent news, historical data, etc.)
    2. Key components that make up the query
    3. The most effective search strategy, with exactly 3 ready-to-use search queries formatted as:
        SEARCH_QUERIES:
        - "query 1"
        - "query 2"
        - "query 3"
    4. Type of sources that would be most relevant
    5. Any potential ambiguities or clarifications needed
    
    Provide a structured analysis with these elements clearly labeled.
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analyze this research query: {query}"}
    ]
    
    try:
        response = await client.generate_data_with_llm(
            messages=messages,
            model="gpt-4o-mini",
            temperature=0.2
        )
        
        analysis_text = response.choices[0].message.content
        
        # Extract structured data from text response using regex
        analysis_json = {
            "intent": "",
            "components": [],
            "search_strategy": "",
            "relevant_sources": [],
            "ambiguities": []
        }
        
        # Extract intent (looking for section 1 or "Primary Intent")
        intent_pattern = r"(?:1\.\s*\*\*(?:Primary\s*)?Intent\*\*:?|Intent:?\s*)[^\n]*(?:\n[^1-5\n][^\n]*)*"
        intent_match = re.search(intent_pattern, analysis_text, re.IGNORECASE)
        if intent_match:
            intent_text = intent_match.group(0)
            # Remove the heading and any bullet points
            intent_text = re.sub(r"1\.\s*\*\*(?:Primary\s*)?Intent\*\*:?|\*\*(?:Primary\s*)?Intent\*\*:?|-\s*", "", intent_text)
            analysis_json["intent"] = intent_text.strip()
        
        # Extract components (looking for section 2 or "Key Components")
        components_pattern = r"(?:2\.\s*\*\*(?:Key\s*)?Components\*\*:?|Components:?\s*)[^\n]*(?:\n[^1-5\n][^\n]*)*"
        components_match = re.search(components_pattern, analysis_text, re.IGNORECASE)
        if components_match:
            components_text = components_match.group(0)
            # Remove the heading
            components_text = re.sub(r"2\.\s*\*\*(?:Key\s*)?Components\*\*:?|\*\*(?:Key\s*)?Components\*\*:?", "", components_text)
            
            # Extract items with bullet points or numbered lists
            components = re.findall(r"(?:^|\n)\s*[-*•]\s*(.*?)(?=\n\s*[-*•]|\n\n|\Z)", components_text, re.DOTALL)
            
            # If no bullet points found, try to extract based on other patterns
            if not components:
                # Try to get items with bold markers
                components = re.findall(r"\*\*(.*?)\*\*:(.*?)(?=\n\s*\*\*|\Z)", components_text, re.DOTALL)
                if components:
                    components = [f"{k.strip()}: {v.strip()}" for k, v in components]
                else:
                    # Last resort: split by newlines and clean up
                    components = [line.strip() for line in components_text.split('\n') if line.strip() and not line.strip().startswith("2.")]
            
            analysis_json["components"] = [c.strip() for c in components if c.strip()]
        
        # Extract search strategy (looking for section 3 or "Search Strategy")
        strategy_pattern = r"(?:3\.\s*\*\*(?:Most\s*Effective\s*)?Search\s*Strategy\*\*:?|Strategy:?\s*)[^\n]*(?:\n[^1-5\n][^\n]*)*"
        strategy_match = re.search(strategy_pattern, analysis_text, re.IGNORECASE)
        if strategy_match:
            strategy_text = strategy_match.group(0)
            # Remove the heading
            strategy_text = re.sub(r"3\.\s*\*\*(?:Most\s*Effective\s*)?Search\s*Strategy\*\*:?|\*\*(?:Most\s*Effective\s*)?Search\s*Strategy\*\*:?", "", strategy_text)
            analysis_json["search_strategy"] = strategy_text.strip()
        
        # Extract relevant sources (looking for section 4 or "Sources")
        sources_pattern = r"(?:4\.\s*\*\*(?:Type\s*of\s*)?Sources[^:]*\*\*:?|Sources:?\s*)[^\n]*(?:\n[^1-5\n][^\n]*)*"
        sources_match = re.search(sources_pattern, analysis_text, re.IGNORECASE)
        if sources_match:
            sources_text = sources_match.group(0)
            # Remove the heading
            sources_text = re.sub(r"4\.\s*\*\*(?:Type\s*of\s*)?Sources[^:]*\*\*:?|\*\*(?:Type\s*of\s*)?Sources[^:]*\*\*:?", "", sources_text)
            
            # Extract items with bullet points
            sources = re.findall(r"(?:^|\n)\s*[-*•]\s*(.*?)(?=\n\s*[-*•]|\n\n|\Z)", sources_text, re.DOTALL)
            
            # If no bullet points found, split by newlines
            if not sources:
                sources = [line.strip() for line in sources_text.split('\n') if line.strip() and not line.strip().startswith("4.")]
            
            analysis_json["relevant_sources"] = [s.strip() for s in sources if s.strip()]
        
        # Extract ambiguities (looking for section 5 or "Ambiguities")
        ambiguities_pattern = r"(?:5\.\s*\*\*(?:Potential\s*)?Ambiguities[^:]*\*\*:?|Ambiguities:?\s*)[^\n]*(?:\n[^1-5\n][^\n]*)*"
        ambiguities_match = re.search(ambiguities_pattern, analysis_text, re.IGNORECASE)
        if ambiguities_match:
            ambiguities_text = ambiguities_match.group(0)
            # Remove the heading
            ambiguities_text = re.sub(r"5\.\s*\*\*(?:Potential\s*)?Ambiguities[^:]*\*\*:?|\*\*(?:Potential\s*)?Ambiguities[^:]*\*\*:?", "", ambiguities_text)
            
            # Extract items with bullet points
            ambiguities = re.findall(r"(?:^|\n)\s*[-*•]\s*(.*?)(?=\n\s*[-*•]|\n\n|\Z)", ambiguities_text, re.DOTALL)
            
            # If no bullet points found, split by newlines
            if not ambiguities:
                ambiguities = [line.strip() for line in ambiguities_text.split('\n') if line.strip() and not line.strip().startswith("5.")]
            
            analysis_json["ambiguities"] = [a.strip() for a in ambiguities if a.strip()]
        
        result = {
            "status": "success",
            "message": "Query analysis completed",
            "analysis": analysis_json,
            "raw_analysis": analysis_text
        }
        
        # Cache the result
        await store_stream_data_in_redis(cache_key, result)
        
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing query: {str(e)}")
        return {
            "status": "error",
            "message": f"Error analyzing query: {str(e)}",
            "analysis": None,
            "raw_analysis": None
        }