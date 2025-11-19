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
    
    async def triage(self, description: str) -> TriageResponse:
        kb_results = self.kb.search(description, top_k=3)
        messages = self._build_messages(description, kb_results)
        tools = self._get_tools()
        response = await self.llm.get_completion(messages, tools)
        result = self._parse_response(response, kb_results)
        return result
    
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