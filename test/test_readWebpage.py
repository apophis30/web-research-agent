# to run : python3 -m test.test_readWebpage

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

# Import the read_webpage function
try:
    from scripts.web.webScraper import read_webpage
    print("Successfully imported read_webpage function")
except ImportError:
    print("Could not import read_webpage function. Please make sure it's in the right location.")
    sys.exit(1)

async def test_read_webpage():
    """Test the read_webpage function with sample URLs"""
    test_user_id = "test_user_123"
    
    # Test with a simple and reliable website
    test_url = "https://example.com"
    
    print(f"\n1. Testing read_webpage with URL: '{test_url}'")
    try:
        result = await read_webpage(test_user_id, test_url)
        print("\nResult:")
        print(json.dumps(result, indent=2))
        
        if result.get('status') == 'success':
            print("\nTesting with same URL again...")
            second_result = await read_webpage(test_user_id, test_url)
            print(f"Second attempt status: {second_result.get('status')}")
            print(f"Title from second attempt: {second_result.get('metadata', {}).get('title')}")
        else:
            print(f"\nFirst attempt failed with message: {result.get('message')}")
    except Exception as e:
        print(f"Error testing simple website: {str(e)}")
    
    # Test with a more complex website
    complex_url = "https://en.wikipedia.org/wiki/Java_(programming_language)"
    print(f"\n2. Testing read_webpage with complex URL: '{complex_url}'")
    try:
        complex_result = await read_webpage(test_user_id, complex_url)
        print("\nResult:")
        print(f"Status: {complex_result.get('status')}")
        print(f"Message: {complex_result.get('message')}")
        print(f"Title: {complex_result.get('metadata', {}).get('title')}")
        
        # Only print first 200 chars of main text to keep output manageable
        if complex_result.get('status') == 'success' and complex_result.get('content'):
            main_text = complex_result.get('content', {}).get('main_text', '')
            if isinstance(main_text, str):
                print(f"Main text (first 300 chars): {main_text[:300]}...")
            
            # Print number of headings and links found
            headings = complex_result.get('content', {}).get('headings', [])
            links = complex_result.get('content', {}).get('links', [])
            tables = complex_result.get('content', {}).get('tables', [])
            
            print(f"Number of headings found: {len(headings)}")
            print(f"Number of links found: {len(links)}")
            print(f"Number of tables found: {len(tables)}")
    except Exception as e:
        print(f"Error testing complex website: {str(e)}")
    
    # Test with an invalid URL
    invalid_url = "https://this-is-not-a-valid-website-12345.com"
    print(f"\n3. Testing read_webpage with invalid URL: '{invalid_url}'")
    try:
        invalid_result = await read_webpage(test_user_id, invalid_url)
        print("\nResult:")
        print(f"Status: {invalid_result.get('status')}")
        print(f"Message: {invalid_result.get('message')}")
    except Exception as e:
        print(f"Error testing invalid website: {str(e)}")
    
    return result

# Run the test case
if __name__ == "__main__":
    print("Starting read_webpage test...")
    asyncio.run(test_read_webpage())
    print("\nTest completed.")