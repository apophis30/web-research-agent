import logging
import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import HTTPException

from config.redis import get_stream_data_from_redis, store_stream_data_in_redis
from config.llmClient import client
from scripts.web.newsAggregator import fetch_news
from scripts.web.webScraper import search_web, scrape_webpage
from scripts.web.analyzer import analyze_query
from scripts.web.web import perform_research, synthesize_information

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Maximum context history to maintain (number of exchanges)
MAX_CONTEXT_LENGTH = 10

# Maximum token count for history before summarization
MAX_TOKEN_COUNT = 4000

async def get_conversation_history(user_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve the conversation history for a user from Redis.
    
    Args:
        user_id (str): The unique identifier for the user.
        
    Returns:
        List[Dict[str, Any]]: The conversation history as a list of message dictionaries.
    """
    cache_key = f"chat_history:{user_id}"
    history = await get_stream_data_from_redis(cache_key)
    
    if not history:
        return []
    
    return history


async def estimate_token_count(messages: List[Dict[str, Any]]) -> int:
    """
    Estimate the token count for a list of messages.
    Simple approximation: 1 token ≈ 4 characters
    
    Args:
        messages (List[Dict[str, Any]]): List of message dictionaries.
        
    Returns:
        int: Estimated token count.
    """
    total_chars = sum(len(msg.get("content", "")) for msg in messages)
    return total_chars // 4  # Simple approximation

async def summarize_conversation_history(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Summarize the conversation history using LLM to reduce token count.
    
    Args:
        history (List[Dict[str, Any]]): The conversation history to summarize.
        
    Returns:
        Dict[str, Any]: A summary message dictionary.
    """
    # Convert history to a format suitable for summarization
    history_text = "\n".join([
        f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}"
        for msg in history
    ])
    
    # Use the LLM client to summarize the history
    try:
        response = await client.generate_data_with_llm(
            messages=[
                {"role": "system", "content": "Summarize the following conversation history concisely while preserving key information, questions, and conclusions:"},
                {"role": "user", "content": history_text}
            ],
            max_tokens=500
        )
        
        summary = response.choices[0].message.content
        
        return {
            "role": "system",
            "content": f"Previous conversation summary: {summary}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error summarizing conversation: {str(e)}")
        return {
            "role": "system",
            "content": f"Previous conversation summary: User and assistant discussed various topics.",
            "timestamp": datetime.now().isoformat()
        }

async def update_conversation_history(user_id: str, new_messages: List[Dict[str, Any]]) -> None:
    """
    Update the conversation history for a user in Redis.
    If token count exceeds limit, summarize older messages.
    
    Args:
        user_id (str): The unique identifier for the user.
        new_messages (List[Dict[str, Any]]): New messages to add to the history.
    """
    cache_key = f"chat_history:{user_id}"
    history = await get_conversation_history(user_id)
    
    # Add new messages
    history.extend(new_messages)
    
    # Check token count
    token_count = await estimate_token_count(history)
    
    if token_count > MAX_TOKEN_COUNT:
        logger.info(f"Token count {token_count} exceeds limit. Summarizing history for user {user_id}")
        
        # Keep the last few exchanges intact
        recent_messages = history[-6:]  # Keep last 3 exchanges (3 user + 3 assistant messages)
        older_messages = history[:-6]
        
        # Summarize older messages
        summary_message = await summarize_conversation_history(older_messages)
        
        # Replace older messages with the summary
        history = [summary_message] + recent_messages
    
    # Store updated history
    await store_stream_data_in_redis(cache_key, history)


async def extract_keywords_from_intent(intent_text: str) -> List[str]:
    """
    Extract relevant keywords from an intent paragraph to help with tool selection.
    
    Args:
        intent_text (str): The intent text from analyze_query.
        
    Returns:
        List[str]: List of extracted keywords.
    """
    # Define keywords associated with different tools
    research_keywords = ["research", "investigate", "comprehensive", "analyze", "study", "examine", "explore"]
    news_keywords = ["news", "latest", "recent", "update", "current events", "today's headlines"]
    search_keywords = ["search", "find", "lookup", "information", "details", "data"]
    scrape_keywords = ["read", "extract", "scrape", "content", "article", "webpage", "website"]
    
    # Lowercase the intent text for case-insensitive matching
    intent_lower = intent_text.lower()
    
    # Extract matches
    found_keywords = []
    for keyword in research_keywords + news_keywords + search_keywords + scrape_keywords:
        if keyword in intent_lower:
            found_keywords.append(keyword)
    
    return found_keywords


async def detect_intent_and_execute_tools(user_id: str, query: str, full_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze the user query, detect the intent, and execute appropriate tools.
    Enhanced to better handle paragraph-style intent descriptions.
    
    Args:
        user_id (str): The unique identifier for the user.
        query (str): The current user query.
        full_history (List[Dict[str, Any]]): The full conversation history.
        
    Returns:
        Dict[str, Any]: The result of the executed tool or intent analysis.
    """
    # First, analyze the query to understand intent
    query_analysis = await analyze_query(user_id, query)
    
    if query_analysis.get("status") == "error":
        return {
            "status": "error",
            "message": f"Error analyzing query: {query_analysis.get('message')}",
            "data": None
        }
    
    # Extract intent and action from the analysis
    intent_text = query_analysis["analysis"].get("intent", "")
    
    # Extract keywords from intent to help determine tool
    keywords = await extract_keywords_from_intent(intent_text)
    logger.info(f"Extracted keywords from intent: {keywords}")
    
    # Check for URLs in the query for scraping
    import re
    url_match = re.search(r'https?://[^\s]+', query)
    has_url = bool(url_match)
    
    # Determine time scope from query for news
    time_indicators = {
        "today": 1,
        "yesterday": 2,
        "last 24 hours": 1,
        "this week": 7,
        "last week": 14,
        "this month": 30,
        "recent": 30
    }
    
    days_back = 7  # Default
    for indicator, days in time_indicators.items():
        if indicator in query.lower():
            days_back = days
            break
    
    # Determine research depth from query
    depth = "standard"  # Default depth
    if any(word in query.lower() for word in ["detailed", "deep", "comprehensive", "thorough"]):
        depth = "deep"
    elif any(word in query.lower() for word in ["quick", "brief", "summary", "short"]):
        depth = "quick"
    
    # Additional keywords for improved web search detection
    weather_keywords = [
    "weather", "temperature", "forecast", "climate", "rain", "sunny", "snow", "humidity",
    "wind", "storm", "tornado", "heatwave", "cold front", "UV index", "air quality", "dew point",
    "chance of rain", "precipitation", "conditions", "weather report", "5-day forecast"
    ]

    info_keywords = [
    "what is", "who is", "tell me about", "information on", "details about", "define", "explain",
    "meaning of", "overview of", "how does", "how do", "why is", "history of", "summary of",
    "examples of", "background on", "describe", "function of", "purpose of", "origin of", "cause of"
    ]

    location_keywords = [
    "in", "at", "near", "around", "close to", "located in", "situated in", "within", 
    "surrounding", "region", "neighborhood", "province", "district", "city", "town", "village",
    "state", "country", "area", "place", "local", "map of", "where is", "directions to", "how far"
    ]

    # Decision pipeline for tool selection
    
    # 1. Check for URL-based scraping first (highest priority if URL is present)
    if has_url and any(kw in keywords for kw in ["read", "extract", "scrape"]):
        url = url_match.group(0)
        logger.info(f"Scraping webpage: {url}")
        result = await scrape_webpage(user_id, url)
        return {
            "status": "success",
            "message": "Webpage scraped",
            "data": result,
            "tool_used": "scrape_webpage"
        }
    
    # 2. Check for research intent
    elif any(kw in keywords for kw in ["research", "investigate", "comprehensive", "analyze", "study"]):
        logger.info(f"Executing research with depth {depth} for query: {query}")
        result = await perform_research(user_id, query, depth)
        return {
            "status": "success",
            "message": "Research completed",
            "data": result,
            "tool_used": "research"
        }
    
    # 3. Check for news intent
    elif any(kw in keywords for kw in ["news", "latest", "recent", "update"]):
        logger.info(f"Fetching news for query: {query} (days_back={days_back})")
        result = await fetch_news(user_id, query, max_results=10, days_back=days_back)
        return {
            "status": "success", 
            "message": "News fetched",
            "data": result,
            "tool_used": "news"
        }
    
    elif any(word in query.lower() for word in weather_keywords):
        logger.info(f"Searching web for weather query: {query}")
        result = await search_web(user_id, query)
        return {
            "status": "success",
            "message": "Web search completed",
            "data": result,
            "tool_used": "web_search"
        }

    elif any(phrase in query.lower() for phrase in info_keywords):
        logger.info(f"Searching web for information query: {query}")
        result = await search_web(user_id, query)
        return {
            "status": "success",
            "message": "Web search completed",
            "data": result,
            "tool_used": "web_search"
        }
    
    elif any(word in query.lower() for word in location_keywords) or any(kw in keywords for kw in ["search", "find", "lookup"]) or not keywords:
        logger.info(f"Searching web for query: {query}")
        result = await search_web(user_id, query)
        return {
            "status": "success",
            "message": "Web search completed",
            "data": result,
            "tool_used": "web_search"
        }
    
    # 5. If we can't determine a clear tool to use, return the analysis
    return {
        "status": "info",
        "message": "No specific tool matched the intent",
        "data": query_analysis,
        "tool_used": None
    }

async def format_tool_result_for_llm(tool_result: Dict[str, Any], query: str) -> str:
    """
    Format the tool execution result to be used in the LLM prompt.
    
    Args:
        tool_result (Dict[str, Any]): The result from the executed tool.
        query (str): The original user query.
        
    Returns:
        str: Formatted result as context for the LLM.
    """
    tool_used = tool_result.get("tool_used")
    data = tool_result.get("data", {})
    
    if tool_used == "research":
        research_result = data.get("result", {})
        answer = research_result.get("answer", "No answer found.")
        sources = research_result.get("sources", [])
        source_list = "\n".join([
            f"- {s.get('name', 'Unknown Source')}: {s.get('url', 'No URL')}"
            for s in sources[:5]  # Limit to top 5 sources
        ])
        
        return f"""RESEARCH RESULTS:
Answer: {answer}

Top Sources:
{source_list}
"""
    
    elif tool_used == "news":
        articles = data.get("articles", [])
        article_list = "\n".join([
            f"- {a.get('title', 'Untitled')}: {a.get('source', 'Unknown Source')} ({a.get('date', 'No date')})"
            for a in articles[:5]  # Limit to top 5 articles
        ])
        
        return f"""NEWS RESULTS:
Top Articles:
{article_list}
"""
    
    elif tool_used == "web_search":
        contexts = data.get("contexts", [])
        result_list = "\n".join([
            f"- {c.get('name', 'Untitled')}: {c.get('snippet', 'No snippet')[:150]}..."
            for c in contexts[:5]  # Limit to top 5 results
        ])
        
        return f"""SEARCH RESULTS:
Top Results:
{result_list}
"""
    
    elif tool_used == "scrape_webpage":
        content = data.get("summarized_content", "No content extracted.")
        metadata = data.get("metadata", {})
        title = metadata.get("title", "Untitled Page")
        url = metadata.get("url", "No URL")
        
        return f"""WEBPAGE CONTENT:
Title: {title}
URL: {url}

Summary:
{content[:500]}...
"""
    
    # For general or unknown tool results
    return f"ANALYSIS: {json.dumps(tool_result.get('data', {}), indent=2)[:500]}..."


async def generate_contextual_response(user_id: str, query: str, history: List[Dict[str, Any]], tool_result: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a response using the LLM based on user query, conversation history, and optional tool execution results.
    
    Args:
        user_id (str): The unique identifier for the user.
        query (str): The current user query.
        history (List[Dict[str, Any]]): The conversation history.
        tool_result (Optional[Dict[str, Any]]): Results from tool execution, if any.
        
    Returns:
        str: The generated response.
    """
    # Create system prompt
    system_prompt = """You are an intelligent research assistant that helps users find information and answer questions.
You have access to several tools:
1. Web search to find current information
2. News aggregation to find recent news articles
3. Webpage scraping to extract detailed content from specific URLs
4. Research capabilities to perform comprehensive investigation on topics

Maintain continuity with previous exchanges. If the user refers to previous information, use it in your response.
Be concise but thorough. Provide specific information rather than general statements when possible.
When tool results are provided, summarize the key points and integrate them into your response naturally.

If you used a tool to answer the query, mention which tool was used and briefly explain why it was chosen.
"""

    # Format conversation history for the LLM context
    formatted_history = []
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role and content:
            formatted_history.append({"role": role, "content": content})
    
    # Add tool result context if available
    tool_context = ""
    if tool_result:
        tool_used = tool_result.get("tool_used")
        tool_context = await format_tool_result_for_llm(tool_result, query)
        # Add tool information to the system prompt
        if tool_used:
            system_prompt += f"\n\nFor the current query, the '{tool_used}' tool was used to gather information."
    
    # Create messages for LLM
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Check token count of history to manage context window
    token_estimate = await estimate_token_count(formatted_history)
    logger.info(f"Estimated token count for history: {token_estimate}")
    
    # Include full history if under threshold, otherwise use recent history
    if token_estimate <= MAX_TOKEN_COUNT:
        messages.extend(formatted_history)
    else:
        # Use only the last few exchanges to save tokens
        messages.extend(formatted_history[-6:])  # Last 3 exchanges (3 user + 3 assistant messages)
    
    # Add the current query with tool context if available
    if tool_context:
        user_message = f"{query}\n\n---\nTool Results:\n{tool_context}\n---"
    else:
        user_message = query
        
    messages.append({"role": "user", "content": user_message})
    
    try:
        # Generate response using the LLM
        response = await client.generate_data_with_llm(
            messages=messages,
            model="gpt-4o-mini",  # Use a powerful model for contextual understanding
            temperature=0.7,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return f"I encountered an error while processing your request. Please try again."


async def chat(user_id: str, message: str) -> Dict[str, Any]:
    """
    Main chat function that processes user messages, maintains context, calls tools, and generates responses.
    
    Args:
        user_id (str): The unique identifier for the user.
        message (str): The user's message.
        
    Returns:
        Dict[str, Any]: The response including generated text and metadata.
    """
    try:
        # Get conversation history
        history = await get_conversation_history(user_id)
        
        # Add user message to history
        user_message = {"role": "user", "content": message, "timestamp": datetime.now().isoformat()}
        
        # Check if we need to add the message before detecting intent
        # This ensures that the history context is available for intent detection
        temp_history = history + [user_message]
        
        # Detect intent and execute tools if needed
        tool_result = await detect_intent_and_execute_tools(user_id, message, temp_history)
        logger.info(f"Tool execution result: {tool_result.get('tool_used')} for query: {message}")
        
        # Now officially update the history with the user message
        await update_conversation_history(user_id, [user_message])
        
        # Generate contextual response
        response_text = await generate_contextual_response(user_id, message, temp_history, tool_result)
        
        # Add assistant response to history
        assistant_message = {
            "role": "assistant", 
            "content": response_text, 
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "tool_used": tool_result.get("tool_used")
            }
        }
        
        # Update history with assistant response
        await update_conversation_history(user_id, [assistant_message])
        
        # Return the final response
        return {
            "status": "success",
            "message": "Response generated successfully",
            "response": response_text,
            "metadata": {
                "tool_used": tool_result.get("tool_used"),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        logger.error(f"Error in chat function: {str(e)}")
        return {
            "status": "error",
            "message": f"Error processing your message: {str(e)}",
            "response": "I'm having trouble processing your request right now. Please try again later.",
            "metadata": {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        }