# to run: python3 -m test.test_chatEngine
import json
import asyncio
import random
import uuid
from datetime import datetime

# Import the chat function from your chatengine
from scripts.web.chatEngine import chat, get_conversation_history, update_conversation_history

class ChatTestCase:
    """Class to manage a single test case for the chat function"""
    def __init__(self, name, query, expected_tool=None, description=None):
        self.name = name
        self.query = query
        self.expected_tool = expected_tool
        self.description = description or name
        self.result = None
    
    def __str__(self):
        return f"Test: {self.name} - {self.description}"

async def test_chat():
    """Test the chat function with various scenarios"""
    # Generate a unique user ID for this test run
    test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    print(f"Starting chat tests with user ID: {test_user_id}")
    
    # Define test cases
    test_cases = [
        ChatTestCase(
            name="basic_query",
            query="What is machine learning?",
            expected_tool="web_search",
            description="Basic informational query that should trigger web search"
        ),
        ChatTestCase(
            name="news_query",
            query="What are the latest news about climate change?",
            expected_tool="news",
            description="News query that should trigger news aggregation"
        ),
        ChatTestCase(
            name="research_query",
            query="Provide a comprehensive analysis of quantum computing advancements",
            expected_tool="research",
            description="Research-oriented query that should trigger in-depth research"
        ),
        ChatTestCase(
            name="webpage_scrape",
            query="Can you read and summarize this article: https://example.com/article",
            expected_tool="scrape_webpage",
            description="URL-based query that should trigger web scraping"
        ),
        ChatTestCase(
            name="follow_up_query",
            query="Tell me more about that",
            expected_tool=None,
            description="Follow-up query that relies on conversation history"
        )
    ]
    
    # Run tests sequentially to build conversation history
    print("\n=== Running Chat Function Tests ===\n")
    for i, test_case in enumerate(test_cases):
        print(f"\n[Test {i+1}/{len(test_cases)}] {test_case}")
        print(f"Query: \"{test_case.query}\"")
        print(f"Expected tool: {test_case.expected_tool or 'None (contextual response)'}")
        
        # Execute the chat function
        start_time = datetime.now()
        result = await chat(test_user_id, test_case.query)
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        # Store result for potential later use
        test_case.result = result
        
        # Print results
        print(f"\nResponse (in {elapsed_time:.2f}s):")
        print(f"{result['response'][:200]}..." if len(result['response']) > 200 else result['response'])
        
        print("\nMetadata:")
        print(json.dumps(result['metadata'], indent=2))
        
        # Verify tool selection
        tool_used = result['metadata'].get('tool_used')
        if test_case.expected_tool:
            if tool_used == test_case.expected_tool:
                print(f"✅ Correct tool used: {tool_used}")
            else:
                print(f"❌ Wrong tool used: Expected {test_case.expected_tool}, got {tool_used}")
        else:
            print(f"Tool used: {tool_used or 'None (contextual response)'}")
        
        # Let's check the conversation history after each test
        if i < len(test_cases) - 1:  # Don't check after the last test to avoid cluttering output
            await check_conversation_history(test_user_id)
            
        # Add a short delay between tests
        await asyncio.sleep(1)
    
    # Final history check
    print("\n=== Final Conversation History Check ===")
    await check_conversation_history(test_user_id)
    
    # Test history summarization by adding many exchanges
    print("\n=== Testing History Summarization ===")
    await test_history_summarization(test_user_id)
    
    return "All tests completed"

async def check_conversation_history(user_id):
    """Check the conversation history for a user"""
    history = await get_conversation_history(user_id)
    print(f"\nConversation history has {len(history)} messages")
    
    # Print a summary of the history
    if history:
        for i, msg in enumerate(history[-4:]):  # Show last 4 messages
            role = msg.get('role', 'unknown')
            content_preview = msg.get('content', '')[:50] + ('...' if len(msg.get('content', '')) > 50 else '')
            print(f"  {i+1}. {role}: {content_preview}")
    else:
        print("  History is empty")
    
    return history

async def test_history_summarization(user_id):
    """Test the conversation history summarization feature"""
    print("Adding multiple exchanges to trigger history summarization...")
    
    # Generate some random exchanges
    for i in range(8):  # 8 exchanges = 16 messages (8 user + 8 assistant)
        query = f"This is test message {i+1}. Please acknowledge it."
        print(f"Adding exchange {i+1}/8...")
        
        # Add user message directly to history
        user_message = {
            "role": "user", 
            "content": query, 
            "timestamp": datetime.now().isoformat()
        }
        await update_conversation_history(user_id, [user_message])
        
        # Add assistant response directly to history
        assistant_message = {
            "role": "assistant", 
            "content": f"I acknowledge test message {i+1}.", 
            "timestamp": datetime.now().isoformat(),
            "metadata": {"tool_used": None}
        }
        await update_conversation_history(user_id, [assistant_message])
    
    # Check the history after adding many messages
    history = await check_conversation_history(user_id)
    
    # See if summarization occurred
    for msg in history:
        if msg.get('role') == 'system' and 'Previous conversation summary' in msg.get('content', ''):
            print("\n✅ History was summarized successfully")
            print(f"Summary message: {msg.get('content')[:100]}...")
            return True
    
    print("\n❌ History was not summarized as expected")
    return False

async def test_error_handling():
    """Test error handling in the chat function"""
    test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    print("\n=== Testing Error Handling ===")
    
    # Test with an empty message
    print("\nTesting with empty message:")
    result = await chat(test_user_id, "")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    
    # Test with a very long message
    print("\nTesting with very long message:")
    long_message = "Test " * 1000  # Create a very long message
    result = await chat(test_user_id, long_message)
    print(f"Status: {result['status']}")
    print(f"Message: {result['message'][:100]}...")
    
    return "Error handling tests completed"

# Run all tests
if __name__ == "__main__":
    # Run the main chat tests
    asyncio.run(test_chat())
    
    # Run error handling tests
    asyncio.run(test_error_handling())
    
    print("\n🎉 All tests completed!")