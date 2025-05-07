import streamlit as st
import requests
import json
import pandas as pd
import time
from typing import List, Dict, Any

# Set page configuration
st.set_page_config(
    page_title="Web Research Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API endpoint (change if deployed elsewhere)
API_URL = "http://localhost:8000"  # Default local FastAPI server

# Sidebar for configuration
with st.sidebar:
    st.title("Web Research Assistant")
    st.markdown("---")
    
    # API configuration
    api_url = st.text_input("API URL", value=API_URL)
    user_id = st.text_input("User ID (optional)", value="streamlit_user")
    
    st.markdown("---")
    st.markdown("### About")
    st.info("This application lets you perform web research, search for information, scrape webpages, and analyze content.")

# Utility functions
def make_api_request(endpoint, data):
    """Make a request to the API"""
    try:
        response = requests.post(f"{api_url}/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        return None

def display_sources(sources: List[Dict[str, Any]]):
    """Display sources in a clean format"""
    if not sources:
        st.warning("No sources found")
        return
    
    for i, source in enumerate(sources):
        with st.expander(f"{i+1}. {source.get('name', 'Unnamed Source')}"):
            st.write(f"**URL:** {source.get('url', 'N/A')}")
            
            if "snippet" in source:
                st.write("**Snippet:**")
                st.write(source["snippet"])
            
            if "summarized_content" in source:
                st.write("**Summary:**")
                st.write(source["summarized_content"])
                
            if "analysis" in source:
                st.write("**Content Analysis:**")
                analysis = source["analysis"]
                analysis_df = pd.DataFrame(
                    [(k, v.get("score", "N/A"), v.get("explanation", "")) 
                     for k, v in analysis.items()],
                    columns=["Criterion", "Score", "Explanation"]
                )
                st.dataframe(analysis_df)

# Main application
st.title("Web Research Assistant")

# Create tabs for different functions
tab1, tab2, tab3, tab4 = st.tabs(["Research", "Web Search", "News", "Webpage Scraper"])

# Research tab
with tab1:
    st.header("Comprehensive Research")
    
    research_query = st.text_area("Research Query", placeholder="Enter your research question...", height=100)
    research_depth_options = ["quick", "standard", "deep"]
    research_depth = st.select_slider("Research Depth", options=research_depth_options, value="standard")
    
    if st.button("Start Research", key="research_button"):
        if research_query:
            with st.spinner("Researching... (This may take some time, especially with 'deep' research)"):
                # Make the API request
                result = make_api_request("research", {
                    "query": research_query,
                    "depth": research_depth,
                    "user_id": user_id
                })
                
                if result and result.get("status") == "success":
                    research_data = result.get("result", {})
                    
                    # Display the query and timestamp
                    st.subheader(f"Research Results for: {research_data.get('query', 'N/A')}")
                    st.caption(f"Completed on: {research_data.get('timestamp', 'N/A')}")
                    
                    # Create tabs for different sections of the research
                    research_tabs = st.tabs(["Answer", "Sources", "Analysis", "Details"])
                    
                    # Tab 1: Answer (main findings)
                    with research_tabs[0]:
                        answer = research_data.get("answer", "No answer generated")
                        # Convert the answer text to Markdown for better formatting
                        st.markdown(answer)
                    
                    # Tab 2: Sources
                    with research_tabs[1]:
                        sources = research_data.get("sources", [])
                        if sources:
                            for i, source in enumerate(sources):
                                with st.expander(f"{i+1}. {source.get('name', 'Unnamed Source')}"):
                                    st.write(f"**URL:** [{source.get('url', 'No URL')}]({source.get('url', '#')})")
                                    st.write(f"**Snippet:** {source.get('snippet', 'No snippet available')}")
                                    
                                    # If there's summarized content, display it
                                    if source.get("summarized_content"):
                                        st.markdown("**Summary:**")
                                        st.markdown(source.get("summarized_content"))
                        else:
                            st.info("No sources provided in the research results.")
                    
                    # Tab 3: Analysis
                    with research_tabs[2]:
                        query_analysis = research_data.get("query_analysis", {})
                        
                        st.subheader("Query Intent")
                        st.write(query_analysis.get("intent", "No intent analysis available."))
                        
                        st.subheader("Query Components")
                        components = query_analysis.get("components", [])
                        if components:
                            for comp in components:
                                st.markdown(f"- {comp}")
                        else:
                            st.info("No component analysis available.")
                        
                        st.subheader("Search Strategy")
                        strategy = query_analysis.get("search_strategy", "")
                        if strategy:
                            st.markdown(f"```\n{strategy}\n```")
                        else:
                            st.info("No search strategy information available.")
                        
                        st.subheader("Relevant Sources")
                        relevant_sources = query_analysis.get("relevant_sources", [])
                        if relevant_sources:
                            for source in relevant_sources:
                                st.markdown(f"- {source}")
                        else:
                            st.info("No relevant sources information available.")
                        
                        st.subheader("Ambiguities")
                        ambiguities = query_analysis.get("ambiguities", [])
                        if ambiguities:
                            for ambiguity in ambiguities:
                                st.markdown(f"- {ambiguity}")
                        else:
                            st.info("No ambiguities identified.")
                    
                    # Tab 4: Additional Details
                    with research_tabs[3]:
                        additional_info = research_data.get("additional_info", {})
                        
                        st.metric("Web Sources", additional_info.get("web_sources", 0))
                        st.metric("News Sources", additional_info.get("news_sources", 0))
                        st.metric("Research Depth", research_data.get("research_depth", "standard"))
                        
                        if additional_info.get("contradictions"):
                            st.subheader("Contradictions Found")
                            st.markdown(additional_info["contradictions"])
                        
                        if additional_info.get("additional_research_suggestions"):
                            st.subheader("Additional Research Suggestions")
                            st.markdown(additional_info["additional_research_suggestions"])
                else:
                    st.error(f"Research failed: {result.get('message', 'Unknown error')}")
        else:
            st.warning("Please enter a research query")

# Web Search tab
with tab2:
    st.header("Quick Web Search")
    
    search_query = st.text_input("Search Query", placeholder="Enter search terms...")
    
    if st.button("Search", key="search_button"):
        if search_query:
            with st.spinner("Searching..."):
                result = make_api_request("search", {
                    "query": search_query,
                    "user_id": user_id
                })
                
                if result:
                    # Display contexts (main search results)
                    if "contexts" in result and result["contexts"]:
                        st.subheader("Search Results")
                        for i, context in enumerate(result["contexts"]):
                            with st.expander(f"{i+1}. {context.get('name', 'Result')}"):
                                st.write(f"**URL:** {context.get('url', 'N/A')}")
                                st.write(f"**Snippet:** {context.get('snippet', 'No snippet available')}")
                    
                    # Display news stories
                    if "stories" in result and result["stories"]:
                        st.subheader("News & Stories")
                        cols = st.columns(2)
                        for i, story in enumerate(result["stories"]):
                            col = cols[i % 2]
                            with col:
                                with st.container():
                                    st.markdown(f"##### {story.get('title', 'Untitled')}")
                                    if "imageUrl" in story:
                                        st.image(story.get('imageUrl'), width=200)
                                    st.write(f"**Source:** {story.get('source', 'Unknown')}")
                                    st.write(f"**Published:** {story.get('date', 'No date')}")
                                    st.write(f"[Read more]({story.get('link', '#')})")
                                    st.markdown("---")
                    
                    # Display related searches
                    if "relatedSearches" in result and result["relatedSearches"]:
                        st.subheader("Related Searches")
                        related_cols = st.columns(3)
                        for i, related in enumerate(result["relatedSearches"]):
                            col = related_cols[i % 3]
                            if "query" in related:
                                col.write(f"- {related['query']}")
                    
                    # Display images
                    if "images" in result and result["images"]:
                        st.subheader("Images")
                        img_cols = st.columns(4)
                        for i, image in enumerate(result["images"]):
                            col = img_cols[i % 4]
                            if "imageUrl" in image:
                                col.image(image.get('imageUrl'), caption=image.get('title', ''), width=150)
                                col.write(f"[View source]({image.get('link', '#')})")
                else:
                    st.error("Search failed or returned no results")
        else:
            st.warning("Please enter a search query")

# News tab
with tab3:
    st.header("News Search")
    
    news_query = st.text_input("News Query", placeholder="Enter news topic...")
    days_back = st.slider("Days Back", min_value=1, max_value=30, value=7)
    max_results = st.slider("Maximum Results", min_value=5, max_value=50, value=20)
    
    if st.button("Search News", key="news_button"):
        if news_query:
            with st.spinner("Fetching news..."):
                # Make the API request with all parameters
                result = make_api_request("news", {
                    "query": news_query,
                    "days_back": days_back,
                    "max_results": max_results,
                    "user_id": user_id
                })
                
                if result and result.get("status") == "success" and "articles" in result:
                    # Display query metadata
                    metadata = result.get("metadata", {})
                    st.subheader(f"News Results for: '{metadata.get('query', news_query)}'")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Results", metadata.get("total_results_available", "N/A"))
                    with col2:
                        st.metric("Results Shown", metadata.get("total_results_returned", len(result["articles"])))
                    with col3:
                        st.metric("Time Range", f"Past {days_back} days")
                    
                    # Create a grid layout for news articles
                    articles = result["articles"]
                    
                    # Option to view as cards or list
                    view_mode = st.radio("View mode", ["Cards", "List"], horizontal=True)
                    
                    if view_mode == "Cards":
                        # Display articles in a grid
                        cols = st.columns(2)  # 2 columns for cards
                        
                        for i, article in enumerate(articles):
                            col = cols[i % 2]
                            with col:
                                with st.container():
                                    st.markdown(f"### {article.get('title', 'Untitled')}")
                                    
                                    # Display thumbnail if available
                                    if article.get('thumbnail'):
                                        st.image(article['thumbnail'], width=300)
                                    
                                    # Display metadata
                                    source_date = []
                                    if article.get('source'):
                                        source_date.append(f"**Source:** {article['source']}")
                                    if article.get('date'):
                                        source_date.append(f"**Date:** {article['date'].split(',')[0]}")
                                    
                                    st.markdown(" | ".join(source_date))
                                    
                                    # Display authors if available
                                    if article.get('authors') and len(article['authors']) > 0:
                                        st.markdown(f"**By:** {', '.join(article['authors'])}")
                                    
                                    # Add read more link
                                    if article.get('link'):
                                        st.markdown(f"[Read More]({article['link']})")
                                    
                                    st.markdown("---")
                    else:
                        # Display as expandable list
                        for i, article in enumerate(articles):
                            if article.get('title'):  # Only display if article has a title
                                with st.expander(f"{i+1}. {article['title']}"):
                                    cols = st.columns([2, 3])
                                    
                                    # Left column for image
                                    with cols[0]:
                                        if article.get('thumbnail'):
                                            st.image(article['thumbnail'], width=200)
                                    
                                    # Right column for details
                                    with cols[1]:
                                        if article.get('source'):
                                            st.write(f"**Source:** {article['source']}")
                                        
                                        if article.get('date'):
                                            st.write(f"**Date:** {article['date']}")
                                            
                                        if article.get('authors') and len(article['authors']) > 0:
                                            st.write(f"**By:** {', '.join(article['authors'])}")
                                        
                                        if article.get('link'):
                                            st.write(f"**URL:** [{article['link']}]({article['link']})")
                else:
                    st.error("News search failed or returned no results")
                    if result and result.get("message"):
                        st.error(f"Error: {result.get('message')}")
        else:
            st.warning("Please enter a news topic")

# Webpage Scraper tab
with tab4:
    st.header("Webpage Scraper")
    
    url_input = st.text_input("Webpage URL", placeholder="Enter full URL (including http:// or https://)")
    selector = st.text_input("Selector Query (Optional)", placeholder="E.g., 'Main content about AI'")
    timeout = st.slider("Timeout (seconds)", min_value=5, max_value=30, value=10)
    
    if st.button("Scrape Webpage", key="scrape_button"):
        if url_input:
            with st.spinner("Scraping webpage... This may take some time for large pages."):
                # Make the API request
                result = make_api_request("scrape", {
                    "url": url_input,
                    "user_id": user_id,
                    "selector_query": selector,
                    "timeout": timeout
                })
                
                if result and result.get("status") == "success":
                    st.subheader("Scraped Content")
                    
                    # Display metadata
                    metadata = result.get("metadata", {})
                    if metadata:
                        st.write(f"**Title:** {metadata.get('title', 'Unknown')}")
                        st.write(f"**URL:** {metadata.get('url', url_input)}")
                    
                    # Display summarized content
                    summarized_content = result.get("summarized_content")
                    if summarized_content:
                        st.markdown("### Summary")
                        st.write(summarized_content)
                    else:
                        st.warning("No content could be extracted from the webpage")
                else:
                    st.error(f"Scraping failed: {result.get('message', 'Unknown error')}")
        else:
            st.warning("Please enter a webpage URL")

# Footer
st.markdown("---")
st.caption("Web Research Assistant © 2025")