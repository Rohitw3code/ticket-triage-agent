import json
import logging
from langchain_core.messages import HumanMessage
from agent.graph import graph

logger = logging.getLogger(__name__)


class TriageAgent:
    def __init__(self):
        pass
    
    async def triage_stream(self, description: str):
        yield json.dumps({"type": "status", "message": "Starting triage with LangGraph"}) + "\n"
        
        initial_state = {
            "messages": [HumanMessage(content=description)],
            "kb_results": "",
            "classification": {}
        }
        
        try:
            async for event in graph.astream(initial_state, stream_mode="updates"):
                for node_name, node_output in event.items():
                    yield json.dumps({
                        "type": "node_start",
                        "node": node_name,
                        "message": f"Executing node: {node_name}"
                    }) + "\n"
                    
                    if node_name == "search_kb" and "kb_results" in node_output:
                        yield json.dumps({
                            "type": "kb_search_complete",
                            "data": node_output["kb_results"]
                        }) + "\n"
                    
                    if node_name == "classify" and "classification" in node_output:
                        yield json.dumps({
                            "type": "classification_complete",
                            "data": node_output["classification"]
                        }) + "\n"
                    
                    if "messages" in node_output:
                        for msg in node_output["messages"]:
                            if hasattr(msg, 'content') and msg.content:
                                yield json.dumps({
                                    "type": "message",
                                    "content": msg.content
                                }) + "\n"
                            
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    yield json.dumps({
                                        "type": "tool_call",
                                        "tool": tool_call.get("name", "unknown"),
                                        "args": tool_call.get("args", {})
                                    }) + "\n"
                    
                    yield json.dumps({
                        "type": "node_complete",
                        "node": node_name
                    }) + "\n"
            
            yield json.dumps({"type": "status", "message": "Triage complete"}) + "\n"
            
        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"