import os
import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv() 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, api_key=None):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def generate_data_with_llm(self, messages, model="gpt-4o-mini", temperature=0.7, max_tokens=None):
        """Generate text using OpenAI's API."""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            raise e

# Initialize LLM client
client = LLMClient()