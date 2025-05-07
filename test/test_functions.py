import asyncio
from scripts.web.web import search_web, analyze_query, analyze_content, scrape_webpage, perform_research

async def test_functions():
    # Test search
    search_results = await search_web("test_user", "climate change solutions")
    print(f"Search returned {len(search_results)} results")

    
    # Test query analysis
    analysis = await analyze_query("test_user", "What are the economic impacts of artificial intelligence?")
    print(f"Query analysis intent: {analysis.get('analysis', {}).get('intent', '')}")
    
    # Test content analysis
    sample_content = "AI is rapidly transforming industries through automation and increased efficiency."
    content_analysis = await analyze_content("test_user", sample_content)
    print(f"Content analysis completed with status: {content_analysis.get('status')}")
    
    # Test full research workflow
    research = await perform_research("test_user", "renewable energy trends", "quick")
    print(f"Research completed with status: {research.get('status')}")

if __name__ == "__main__":
    asyncio.run(test_functions())