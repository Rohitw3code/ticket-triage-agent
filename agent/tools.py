from langchain_core.tools import tool
from typing import List, Dict
import json
from kb.search import KnowledgeBase


kb = KnowledgeBase()


@tool
def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for similar tickets and known issues."""
    
    results = kb.search(query, top_k=3)
    
    if not results:
        return "No matching known issues found in the knowledge base."
    
    output = "Found related known issues:\n"
    for item in results:
        output += f"- ID: {item['id']} | {item['title']} | Similarity: {item['score']:.2f}\n"
        output += f"  Recommended action: {item['recommended_action']}\n"
    
    return output


@tool
def classify_ticket(
    summary: str,
    category: str,
    severity: str,
    issue_type: str,
    next_action: str
) -> str:
    """Classify and triage a support ticket with all required fields.
    
    Args:
        summary: 1-2 line overall summary of the ticket
        category: One of Billing, Login, Performance, Bug, Question/How-To
        severity: One of Low, Medium, High, Critical
        issue_type: Either known_issue or new_issue
        next_action: Suggested next step for handling this ticket
    """
    
    result = {
        "summary": summary,
        "category": category,
        "severity": severity,
        "issue_type": issue_type,
        "next_action": next_action
    }
    
    return json.dumps(result)
