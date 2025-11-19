# agent/orchestrator.py

import json
import logging
from typing import List, Dict
from agent.lm_client import LLMClient
from agent.models import TriageResponse, KnownIssue
from agent.prompts import get_triage_prompt, get_kb_context
from kb.search import KnowledgeBase

logger = logging.getLogger(__name__)


class TriageAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.kb = KnowledgeBase()
        self.kb_entries = self.kb.load_kb()
    
    async def triage_stream(self, description: str):
        from agent.graph import graph
        from langchain_core.messages import HumanMessage
        
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
    
    def _search_kb_with_stream(self, description: str):
        events = []
        
        def callback(event):
            events.append(event)
        
        kb_results = self.kb.search(description, top_k=3, stream_callback=callback)
        
        for event in events:
            yield event
        
        yield {"type": "results", "results": kb_results}
    
    def _build_messages(self, description: str, kb_results: List[Dict]) -> List[Dict]:
        kb_context = get_kb_context(kb_results)
        system_prompt = get_triage_prompt(kb_context)
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": description}
        ]
    
    def _get_tools(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "classify_ticket",
                    "description": "Extract and classify ticket information including summary, category, severity, issue type, and next action",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "1-2 line overall summary combining the user's issue with relevant known issues found"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["Billing", "Login", "Performance", "Bug", "Question/How-To"],
                                "description": "Ticket category"
                            },
                            "severity": {
                                "type": "string",
                                "enum": ["Low", "Medium", "High", "Critical"],
                                "description": "Issue severity level"
                            },
                            "issue_type": {
                                "type": "string",
                                "enum": ["known_issue", "new_issue"],
                                "description": "Whether this matches a known issue or is new"
                            },
                            "next_action": {
                                "type": "string",
                                "description": "Suggested next step for handling this ticket"
                            }
                        },
                        "required": ["summary", "category", "severity", "issue_type", "next_action"]
                    }
                }
            }
        ]
    
    def _parse_response(self, response, kb_results: List[Dict]) -> TriageResponse:
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
        else:
            content = response.choices[0].message.content
            try:
                args = json.loads(content)
            except:
                raise ValueError("Could not parse LLM response")
        
        related_issues = [
            KnownIssue(
                id=item['id'],
                title=item['title'],
                similarity_score=item['score']
            )
            for item in kb_results[:3]
        ]
        
        return TriageResponse(
            summary=args['summary'],
            category=args['category'],
            severity=args['severity'],
            issue_type=args['issue_type'],
            related_issues=related_issues,
            next_action=args['next_action']
        )