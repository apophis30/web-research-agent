# to run : python3 -m test.test_scrapePage

import json
import asyncio
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the parent directory to sys.path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the fixed function
# First, make sure to save the fixed_scraper.py in your scripts/web directory
# and import it properly
try:
    from scripts.web.webScraper import scrape_webpage
    print("Successfully imported fixed scrape_webpage function")
except ImportError:
    print("Could not import fixed_scraper.py. Please make sure it's in the right location.")
    print("Attempting to fallback to original function...")
    try:
        from scripts.web.webScraper import scrape_webpage
        print("Imported original scrape_webpage function")
    except ImportError:
        print("Could not import scrape_webpage function. Please check your import paths.")
        sys.exit(1)

async def test_scrape_webpage():
    """Test the fixed scrape_webpage function with sample URLs"""
    test_user_id = "test_user_123"
    
    # Test with a simple and reliable website
    test_url = "https://example.com"
    
    print(f"\n1. Testing scrape_webpage with URL: '{test_url}'")
    try:
        result = await scrape_webpage(test_user_id, test_url)
        print("\nResult:")
        print(json.dumps(result, indent=2))
        
        if result.get('status') == 'success':
            print("\nTesting cache retrieval...")
            cached_result = await scrape_webpage(test_user_id, test_url)
            print(f"Retrieved from cache: {cached_result.get('status') == 'success'}")
            print(f"Title from cache: {cached_result.get('metadata', {}).get('title')}")
        else:
            print(f"\nFirst attempt failed with message: {result.get('message')}")
    except Exception as e:
        print(f"Error testing simple website: {str(e)}")
    
    # Test with a more complex website
    complex_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    print(f"\n2. Testing scrape_webpage with complex URL: '{complex_url}'")
    try:
        complex_result = await scrape_webpage(test_user_id, complex_url, timeout=15)
        print("\nResult:")
        print(f"Status: {complex_result.get('status')}")
        print(f"Message: {complex_result.get('message')}")
        print(f"Title: {complex_result.get('metadata', {}).get('title')}")
        # Only print first 200 chars of summary to keep output manageable
        summary = complex_result.get('summarized_content', '')
        print(f"Summary (first 200 chars): {summary[:200]}...")
    except Exception as e:
        print(f"Error testing complex website: {str(e)}")
    
    return result

# Run the test case
if __name__ == "__main__":
    print("Starting scrape_webpage test...")
    asyncio.run(test_scrape_webpage())
    print("\nTest completed.")