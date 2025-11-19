# agent/orchestrator.py

import json
import logging
from typing import List, Dict
from agent.lm_client import LLMClient
from agent.models import TriageResponse, KnownIssue
from kb.search import KnowledgeBase

logger = logging.getLogger(__name__)


class TriageAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.kb = KnowledgeBase()
        self.kb_entries = self.kb.load_kb()
    
    async def triage(self, description: str) -> TriageResponse:
        """Main triage logic"""
        
        # Step 1: Search knowledge base
        kb_results = self.kb.search(description, top_k=3)
        
        # Step 2: Get LLM analysis with tool calling
        messages = self._build_messages(description, kb_results)
        tools = self._get_tools()
        
        response = await self.llm.get_completion(messages, tools)
        
        # Step 3: Parse response
        result = self._parse_response(response, kb_results)
        
        return result
    
    def _build_messages(self, description: str, kb_results: List[Dict]) -> List[Dict]:
        """Build prompt messages"""
        
        kb_context = "\n".join([
            f"- {item['title']} (ID: {item['id']}, Score: {item['score']:.2f})"
            for item in kb_results
        ])
        
        system_prompt = f"""You are a support ticket triage assistant. Analyze tickets and classify them.

Available categories: Billing, Login, Performance, Bug, Question/How-To
Available severities: Low, Medium, High, Critical

Known issues from knowledge base:
{kb_context if kb_context else "No matching known issues found"}

Your task:
1. Provide a 1-2 line summary
2. Classify the category
3. Determine severity
4. Decide if this is a known_issue or new_issue (based on KB matches with score > 0.5)
5. Suggest next action

Response format:
{{
    "summary": "brief summary",
    "category": "category name",
    "severity": "severity level",
    "issue_type": "known_issue or new_issue",
    "next_action": "what to do next"
}}"""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Ticket description: {description}"}
        ]
    
    def _get_tools(self) -> List[Dict]:
        """Define function calling schema"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "classify_ticket",
                    "description": "Classify and triage a support ticket",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "1-2 line summary of the issue"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["Billing", "Login", "Performance", "Bug", "Question/How-To"]
                            },
                            "severity": {
                                "type": "string",
                                "enum": ["Low", "Medium", "High", "Critical"]
                            },
                            "issue_type": {
                                "type": "string",
                                "enum": ["known_issue", "new_issue"]
                            },
                            "next_action": {
                                "type": "string",
                                "description": "Recommended next step"
                            }
                        },
                        "required": ["summary", "category", "severity", "issue_type", "next_action"]
                    }
                }
            }
        ]
    
    def _parse_response(self, response, kb_results: List[Dict]) -> TriageResponse:
        """Parse LLM response into structured output"""
        
        # Check if tool was called
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
        else:
            # Fallback: try to parse from content
            content = response.choices[0].message.content
            try:
                args = json.loads(content)
            except:
                raise ValueError("Could not parse LLM response")
        
        # Build related issues list
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