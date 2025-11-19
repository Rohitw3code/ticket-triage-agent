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
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3
            }
            
            if tools:
                params["tools"] = tools
                params["tool_choice"] = {"type": "function", "function": {"name": "classify_ticket"}}
            
            response = self.client.chat.completions.create(**params)
            return response
        
        except Exception as e:
            logger.error(f"LLM error: {e}")
            raise