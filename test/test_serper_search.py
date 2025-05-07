import asyncio
from scripts.web.web import _search_with_serper

# Test function to see the output
async def test_serper_search():
    query = "latest news on India Pakistan Tensions"
    result = await _search_with_serper(query)
    
    # Print the result to see what comes back from the API
    print(result)

# Run the test
asyncio.run(test_serper_search())