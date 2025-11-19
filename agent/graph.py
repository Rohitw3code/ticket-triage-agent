from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from agent.tools import search_knowledge_base, classify_ticket
from app.config import get_settings


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    kb_results: str
    classification: dict


settings = get_settings()


def search_kb_node(state: AgentState):
    messages = state["messages"]
    user_query = messages[-1].content
    
    kb_results = search_knowledge_base.invoke({"query": user_query})
    
    return {
        "kb_results": kb_results,
        "messages": [SystemMessage(content=f"Knowledge base search results:\n{kb_results}")]
    }


def classify_node(state: AgentState):
    kb_results = state.get("kb_results", "")
    user_query = state["messages"][0].content
    
    prompt = f"""You are a support ticket triage assistant.

User ticket: {user_query}

{kb_results}

Task:
1. Write a 1-2 line summary combining the user's issue with relevant known issues
2. Classify category: Billing, Login, Performance, Bug, or Question/How-To
3. Assign severity: Low, Medium, High, or Critical
4. Determine issue_type: known_issue (if similarity > 0.5) or new_issue
5. Suggest next_action:
   - For known issues: "Attach KB article [ID] and respond to user" or "Escalate to [team] per [ID]"
   - For new issues: "Escalate to [team]" or "Ask customer for logs/screenshots"

Call the classify_ticket tool with these fields."""
    
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.3
    )
    
    llm_with_tools = llm.bind_tools([classify_ticket], tool_choice="classify_ticket")
    
    response = llm_with_tools.invoke([SystemMessage(content=prompt)])
    
    if response.tool_calls:
        tool_call = response.tool_calls[0]
        classification = tool_call["args"]
    else:
        classification = {}
    
    return {
        "classification": classification,
        "messages": [response]
    }


def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("search_kb", search_kb_node)
    workflow.add_node("classify", classify_node)
    
    workflow.set_entry_point("search_kb")
    workflow.add_edge("search_kb", "classify")
    workflow.add_edge("classify", END)
    
    return workflow.compile()


graph = build_graph()
