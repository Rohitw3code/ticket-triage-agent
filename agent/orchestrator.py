import json
import logging
import uuid
from langchain_core.messages import HumanMessage
from agent.graph import graph

logger = logging.getLogger(__name__)


class TriageAgent:
    def __init__(self):
        self.active_threads = {}  # Store thread_id -> state mapping
    
    async def triage_stream(self, description: str, thread_id: str = None):
        """Start a new triage or continue an existing one."""
        
        # Generate or use existing thread_id
        if not thread_id:
            thread_id = str(uuid.uuid4())
            is_new = True
        else:
            is_new = False
        
        config = {"configurable": {"thread_id": thread_id}}
        
        if is_new:
            yield json.dumps({
                "type": "status", 
                "message": "🤖 I'm working on it... Please wait a moment while I embed the knowledge base",
                "thread_id": thread_id
            }) + "\n"
            
            initial_state = {
                "messages": [HumanMessage(content=description)],
                "kb_results": "",
                "classification": {},
                "needs_more_info": False,
                "additional_details": "",
                "interrupt_question": ""
            }
            
            stream_input = initial_state
        else:
            yield json.dumps({
                "type": "status", 
                "message": "Resuming triage...",
                "thread_id": thread_id
            }) + "\n"
            
            # When resuming, pass None to continue from checkpoint
            stream_input = None
        
        try:
            async for event in graph.astream(stream_input, config=config, stream_mode="updates"):
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
                    
                    if node_name == "analyze" and node_output.get("needs_more_info"):
                        yield json.dumps({
                            "type": "interrupt",
                            "question": node_output.get("interrupt_question", ""),
                            "thread_id": thread_id,
                            "message": "Agent needs more information to continue"
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
            
            # Check if we're interrupted
            current_state = graph.get_state(config)
            
            # Check if we're actually interrupted (needs_more_info is True and no classification)
            if (current_state.values.get("needs_more_info") and 
                not current_state.values.get("classification")):
                # We're interrupted, waiting for input
                yield json.dumps({
                    "type": "status", 
                    "message": "Waiting for user response...",
                    "thread_id": thread_id
                }) + "\n"
            else:
                # Completed
                yield json.dumps({
                    "type": "status", 
                    "message": "Triage complete"
                }) + "\n"
            
        except Exception as e:
            logger.error(f"Error in triage_stream: {e}", exc_info=True)
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"
    
    async def resume_with_details(self, thread_id: str, additional_details: str):
        """Resume an interrupted workflow with additional user details."""
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Get current state
            current_state = graph.get_state(config)
            
            if not current_state:
                raise ValueError(f"No workflow found for thread_id: {thread_id}")
            
            # Update state with additional details
            graph.update_state(
                config,
                {
                    "additional_details": additional_details,
                    "needs_more_info": False,
                    "messages": [HumanMessage(content=f"Additional details: {additional_details}")]
                }
            )
            
            # Continue streaming from where we left off
            async for chunk in self.triage_stream(description="", thread_id=thread_id):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in resume_with_details: {e}", exc_info=True)
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"