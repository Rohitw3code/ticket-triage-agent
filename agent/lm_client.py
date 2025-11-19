from openai import OpenAI
import logging
import json
from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def get_completion_stream(self, messages, tools=None):
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "stream": True
            }
            
            if tools:
                params["tools"] = tools
                params["tool_choice"] = {"type": "function", "function": {"name": "classify_ticket"}}
            
            yield json.dumps({"type": "status", "message": "Starting LLM completion"}) + "\n"
            
            stream = self.client.chat.completions.create(**params)
            
            tool_calls = {}
            content_buffer = ""
            
            for chunk in stream:
                delta = chunk.choices[0].delta
                
                if delta.content:
                    content_buffer += delta.content
                    yield json.dumps({"type": "content", "data": delta.content}) + "\n"
                
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        idx = tool_call.index
                        if idx not in tool_calls:
                            tool_calls[idx] = {
                                "id": tool_call.id or "",
                                "name": "",
                                "arguments": ""
                            }
                            if tool_call.function and tool_call.function.name:
                                tool_calls[idx]["name"] = tool_call.function.name
                                yield json.dumps({
                                    "type": "tool_call_start",
                                    "tool": tool_call.function.name,
                                    "index": idx
                                }) + "\n"
                        
                        if tool_call.function and tool_call.function.arguments:
                            tool_calls[idx]["arguments"] += tool_call.function.arguments
                            yield json.dumps({
                                "type": "tool_call_delta",
                                "index": idx,
                                "data": tool_call.function.arguments
                            }) + "\n"
            
            for idx, tool_call in tool_calls.items():
                try:
                    args = json.loads(tool_call["arguments"])
                    yield json.dumps({
                        "type": "tool_call_complete",
                        "tool": tool_call["name"],
                        "index": idx,
                        "arguments": args
                    }) + "\n"
                except:
                    pass
            
            yield json.dumps({"type": "status", "message": "LLM completion finished"}) + "\n"
            yield json.dumps({"type": "tool_calls", "data": tool_calls}) + "\n"
            
        except Exception as e:
            logger.error(f"LLM error: {e}")
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"
            raise