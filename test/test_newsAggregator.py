# to run : python3 -m test.test_newsAggregator
import asyncio
from scripts.web.newsAggregator import fetch_news

async def main():
    news = await fetch_news("user123", "virat kohli and avneet kaur", max_results=10, days_back=3)
    print(f"Found {len(news['articles'])} articles")
    
    # Example with potentially problematic query
    news = await fetch_news("user123", "SELECT * FROM users; --", max_results=5, days_back=1)
    print(f"Found {len(news['articles'])} articles with sanitized query")

if __name__ == "__main__":
    asyncio.run(main())