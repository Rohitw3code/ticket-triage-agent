from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agent.tools import search_knowledge_base, classify_ticket
from agent.utils import retry_with_backoff, handle_llm_error, LLMError
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)


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


@retry_with_backoff()
def call_llm_with_retry(llm, messages):
    """Wrapper function for LLM calls with retry logic."""
    return llm.invoke(messages)


def analyze_node(state: AgentState):
    """Analyze if we need more information from the user."""
    kb_results = state.get("kb_results", "")
    user_query = state["messages"][0].content
    additional_details = state.get("additional_details", "")
    
    # Build context with additional details if provided
    full_context = user_query
    if additional_details:
        full_context += f"\n\nAdditional details provided by user:\n{additional_details}"
    
    try:
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=settings.OPENAI_TEMPERATURE,
            timeout=settings.OPENAI_TIMEOUT,
            max_retries=0  # We handle retries ourselves
        )
        
        # First, check if we need more information
        analysis_prompt = f"""Analyze this support ticket and determine if you have enough information to match it with the knowledge base results.

Ticket: {full_context}

{kb_results}

Your task:
1. Look at the knowledge base results above
2. Determine if you can confidently match the ticket to one of the known issues OR classify it as a new issue
3. Only ask for more information if:
   - The ticket is extremely vague (e.g., "something is broken", "not working")
   - You cannot determine which category it belongs to
   - The description is so unclear that you're unsure if it matches any KB entry or not

If you have enough information to proceed (even if no KB match is found), respond with:
PROCEED

If you genuinely need more information to determine relevance to KB or categorize, respond with:
NEED_MORE_INFO: <specific question to ask the user>

Examples:
- "App is slow" -> PROCEED (can classify as Performance, even without exact KB match)
- "Getting error 500 on checkout" -> PROCEED (specific enough, clear category)
- "Login not working" -> PROCEED (clear category, can match or escalate)
- "Something is broken" -> NEED_MORE_INFO: What exactly isn't working? Can you describe which feature or page you're having trouble with?
- "Issue" -> NEED_MORE_INFO: Can you please describe the issue you're experiencing? What were you trying to do when the problem occurred?
- "Help" -> NEED_MORE_INFO: What do you need help with? Please describe your question or issue.
- "Mobile error" -> PROCEED (vague but has context - mobile + error, can classify)

Only interrupt if the ticket provides NO actionable information."""
        
        analysis_response = call_llm_with_retry(llm, [SystemMessage(content=analysis_prompt)])
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
    
    except LLMError as e:
        logger.error(f"LLM error in analyze_node: {e}")
        error_info = handle_llm_error(e)
        return {
            "needs_more_info": False,
            "messages": [AIMessage(content=f"⚠️ Error analyzing ticket: {error_info['message']}. Proceeding with best-effort classification.")]
        }
    
    except Exception as e:
        logger.error(f"Unexpected error in analyze_node: {e}", exc_info=True)
        return {
            "needs_more_info": False,
            "messages": [AIMessage(content="⚠️ An error occurred during analysis. Proceeding with classification...")]
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
    
    try:
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=settings.OPENAI_TEMPERATURE,
            timeout=settings.OPENAI_TIMEOUT,
            max_retries=0  # We handle retries ourselves
        )
        
        llm_with_tools = llm.bind_tools([classify_ticket], tool_choice="classify_ticket")
        
        response = call_llm_with_retry(llm_with_tools, [SystemMessage(content=prompt)])
        
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            classification = tool_call["args"]
        else:
            # Fallback classification if tool call fails
            classification = {
                "summary": full_context[:100],
                "category": "Bug",
                "severity": "Medium",
                "issue_type": "new_issue",
                "next_action": "Manual review required - classification incomplete"
            }
            logger.warning("No tool calls in response, using fallback classification")
        
        return {
            "classification": classification,
            "messages": [response]
        }
    
    except LLMError as e:
        logger.error(f"LLM error in classify_node: {e}")
        error_info = handle_llm_error(e)
        
        # Return fallback classification
        fallback_classification = {
            "summary": full_context[:100] + "...",
            "category": "Bug",
            "severity": "Medium",
            "issue_type": "new_issue",
            "next_action": f"Manual review required - {error_info['message']}"
        }
        
        return {
            "classification": fallback_classification,
            "messages": [AIMessage(content=f"⚠️ Classification completed with fallback due to error: {error_info['message']}")]
        }
    
    except Exception as e:
        logger.error(f"Unexpected error in classify_node: {e}", exc_info=True)
        
        # Return minimal fallback classification
        fallback_classification = {
            "summary": "Error during classification",
            "category": "Bug",
            "severity": "Medium",
            "issue_type": "new_issue",
            "next_action": "Manual review required - unexpected error"
        }
        
        return {
            "classification": fallback_classification,
            "messages": [AIMessage(content="⚠️ An error occurred during classification. Please review manually.")]
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
    # Only interrupt at END when needs_more_info is True (handled by conditional edge)
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


graph = build_graph()
