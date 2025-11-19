from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agent.tools import search_knowledge_base, classify_ticket
from app.config import get_settings


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    kb_results: str
    classification: dict
    needs_more_info: bool
    additional_details: str
    interrupt_question: str


settings = get_settings()


def search_kb_node(state: AgentState):
    messages = state["messages"]
    user_query = messages[-1].content
    
    kb_results = search_knowledge_base.invoke({"query": user_query})
    
    return {
        "kb_results": kb_results,
        "messages": [SystemMessage(content=f"Knowledge base search results:\n{kb_results}")]
    }


def analyze_node(state: AgentState):
    """Analyze if we need more information from the user."""
    kb_results = state.get("kb_results", "")
    user_query = state["messages"][0].content
    additional_details = state.get("additional_details", "")
    
    # Build context with additional details if provided
    full_context = user_query
    if additional_details:
        full_context += f"\n\nAdditional details provided by user:\n{additional_details}"
    
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.3
    )
    
    # First, check if we need more information
    analysis_prompt = f"""Analyze this support ticket and determine if you need more information to properly triage it.

Ticket: {full_context}

{kb_results}

If the ticket is vague, missing critical details (like error messages, affected features, device info, steps to reproduce), 
or you cannot confidently classify it, respond with:
NEED_MORE_INFO: <specific question to ask the user>

Otherwise, respond with:
PROCEED

Examples:
- "App is slow" -> NEED_MORE_INFO: Can you provide more details? Which specific feature is slow? What device/browser are you using? When did this start?
- "Getting error 500 on checkout" -> PROCEED (specific enough)
- "Something is broken" -> NEED_MORE_INFO: What exactly is broken? Can you describe the issue and what you were trying to do?
"""
    
    analysis_response = llm.invoke([SystemMessage(content=analysis_prompt)])
    content = analysis_response.content.strip()
    
    if content.startswith("NEED_MORE_INFO:"):
        question = content.replace("NEED_MORE_INFO:", "").strip()
        return {
            "needs_more_info": True,
            "interrupt_question": question,
            "messages": [AIMessage(content=f"🤔 I need more information to properly classify this ticket.\n\nQuestion: {question}")]
        }
    else:
        return {
            "needs_more_info": False,
            "messages": [AIMessage(content="Proceeding with classification...")]
        }


def classify_node(state: AgentState):
    kb_results = state.get("kb_results", "")
    user_query = state["messages"][0].content
    additional_details = state.get("additional_details", "")
    
    # Build full context
    full_context = user_query
    if additional_details:
        full_context += f"\n\nAdditional details: {additional_details}"
    
    prompt = f"""You are a support ticket triage assistant.

User ticket: {full_context}

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


def should_interrupt(state: AgentState) -> Literal["interrupt", "classify"]:
    """Decide whether to interrupt for more info or proceed to classification."""
    if state.get("needs_more_info", False) and not state.get("additional_details"):
        return "interrupt"
    return "classify"


def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("search_kb", search_kb_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("classify", classify_node)
    
    workflow.set_entry_point("search_kb")
    workflow.add_edge("search_kb", "analyze")
    
    # Conditional edge: interrupt if more info needed, otherwise classify
    workflow.add_conditional_edges(
        "analyze",
        should_interrupt,
        {
            "interrupt": END,  # Stop here and wait for user input
            "classify": "classify"
        }
    )
    
    workflow.add_edge("classify", END)
    
    # Add checkpointer for state persistence
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory, interrupt_before=["classify"])


graph = build_graph()
