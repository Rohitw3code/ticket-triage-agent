from openai import OpenAI
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def get_completion(self, messages, tools=None):
        """Get completion from OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                temperature=0.3
            )
            return response
        
        except Exception as e:
            logger.error(f"LLM error: {e}")
            raise