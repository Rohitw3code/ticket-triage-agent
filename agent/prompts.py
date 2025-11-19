def get_triage_prompt(kb_context: str) -> str:
    return f"""You are a support ticket triage assistant. Your job is to analyze support tickets and provide structured classification.
        {kb_context}

        Your task is to:

        1. Summary: Generate a concise 1-2 line summary that captures the core issue from the user's description and relates it to any similar known issues found in the knowledge base.

        2. Category: Classify the ticket into one of these categories:
        - Billing: Payment issues, invoices, subscriptions
        - Login: Authentication, password, 2FA problems
        - Performance: Slow loading, timeouts, database issues
        - Bug: Application errors, crashes, unexpected behavior
        - Question/How-To: User asking how to do something

        3. Severity: Assign severity level:
        - Critical: Service completely down, affects many users
        - High: Major functionality broken, affects workflow
        - Medium: Feature not working but workarounds exist
        - Low: Minor issues, cosmetic problems, general questions

        4. Issue Type: Determine if this is:
        - known_issue: Similar issue exists in KB with similarity score > 0.5
        - new_issue: No matching issue found or similarity score < 0.5

        5. Next Action: Suggest specific next step:
        - For known issues with KB articles: "Attach KB article [ID] and respond to user"
        - For known issues needing escalation: "Escalate to [team] team; link to [ID]"
        - For new issues: "Escalate to [team] team" or "Ask customer for logs/screenshots"

        Use the classify_ticket function to provide your structured analysis."""


def get_kb_context(kb_results: list) -> str:
    if not kb_results:
        return "No matching known issues found in the knowledge base."
    
    context = "Related known issues found:\n"
    for item in kb_results:
        context += f"- ID: {item['id']} | {item['title']} | Similarity: {item['score']:.2f}\n"
    
    return context.strip()
