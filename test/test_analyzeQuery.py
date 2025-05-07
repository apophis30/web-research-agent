# to run : python3 -m test.test_analyzeQuery

import json
import asyncio
from scripts.web.analyzer import analyze_query

async def test_analyze_query():
    """Test the analyze_query function with a sample query"""
    test_user_id = "test_user_123"
    test_query = "Who is Priety Zinta?"
    
    print(f"Testing analyze_query with query: '{test_query}'")
    result = await analyze_query(test_user_id, test_query)
    
    print("\nResult:")
    print(json.dumps(result, indent=2))
    
    # Test cache retrieval
    print("\nTesting cache retrieval...")
    cached_result = await analyze_query(test_user_id, test_query)
    print(f"Retrieved from cache: {cached_result['status'] == 'success'}")
    
    return result

# Run the test case
if __name__ == "__main__":
    asyncio.run(test_analyze_query())