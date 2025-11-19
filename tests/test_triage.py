import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
from agent.orchestrator import TriageAgent


client = TestClient(app)


# ============================================================================
# API Endpoint Tests
# ============================================================================

def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()


@pytest.mark.slow
def test_triage_stream_basic(mock_async_openai_client):
    """Test basic streaming triage request with valid description"""
    payload = {"description": "Getting error 500 on mobile checkout"}
    response = client.post("/triage/stream", json=payload)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-ndjson"
    
    # Parse NDJSON stream
    events = []
    for line in response.iter_lines():
        if line:
            events.append(json.loads(line))
    
    assert len(events) > 0
    
    # Check for expected event types
    event_types = [event["type"] for event in events]
    assert "status" in event_types


def test_triage_stream_empty_description():
    """Test triage with empty description returns 400"""
    payload = {"description": ""}
    response = client.post("/triage/stream", json=payload)
    
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_triage_stream_whitespace_only():
    """Test triage with whitespace-only description returns 400"""
    payload = {"description": "   \n\t  "}
    response = client.post("/triage/stream", json=payload)
    
    assert response.status_code == 400


def test_triage_stream_very_long_description():
    """Test triage with description exceeding max length returns 400"""
    payload = {"description": "A" * 10000}  # Exceeds MAX_DESCRIPTION_LENGTH
    response = client.post("/triage/stream", json=payload)
    
    assert response.status_code == 400
    assert "too long" in response.json()["detail"].lower()


@pytest.mark.slow
def test_triage_stream_specific_issue(mock_async_openai_client):
    """Test triage with specific issue description"""
    payload = {"description": "Login fails with incorrect password error"}
    response = client.post("/triage/stream", json=payload)
    
    assert response.status_code == 200
    
    events = []
    classification_found = False
    
    for line in response.iter_lines():
        if line:
            event = json.loads(line)
            events.append(event)
            
            # Check if classification is present
            if event.get("type") == "classification_complete":
                classification = event["data"]
                assert "summary" in classification
                assert "category" in classification
                assert "severity" in classification
                assert "issue_type" in classification
                assert "next_action" in classification
                classification_found = True
    
    # Should either have classification or interrupt
    event_types = [e["type"] for e in events]
    assert classification_found or "interrupt" in event_types


@pytest.mark.slow
def test_triage_stream_vague_query(mock_async_openai_client):
    """Test triage with vague query might trigger interrupt"""
    payload = {"description": "help"}
    response = client.post("/triage/stream", json=payload)
    
    assert response.status_code == 200
    
    events = []
    for line in response.iter_lines():
        if line:
            events.append(json.loads(line))
    
    # Check if interrupt or classification event is present
    event_types = [event["type"] for event in events]
    assert len(event_types) > 0


def test_resume_endpoint_missing_thread_id():
    """Test resume endpoint without thread_id returns 400"""
    payload = {"thread_id": "", "additional_details": "Some details"}
    response = client.post("/triage/resume", json=payload)
    
    assert response.status_code == 400


def test_resume_endpoint_empty_details():
    """Test resume endpoint with empty additional_details returns 400"""
    payload = {"thread_id": "test-123", "additional_details": ""}
    response = client.post("/triage/resume", json=payload)
    
    assert response.status_code == 400


# ============================================================================
# Agent Logic Tests
# ============================================================================

@pytest.mark.asyncio
async def test_agent_triage_stream():
    """Test agent triage stream returns events"""
    agent = TriageAgent()
    description = "Getting error 500 on mobile checkout"
    
    events = []
    async for event_str in agent.triage_stream(description):
        event = json.loads(event_str.strip())
        events.append(event)
    
    assert len(events) > 0
    
    # Verify thread_id is generated
    status_events = [e for e in events if e.get("type") == "status"]
    assert any("thread_id" in e for e in status_events)


@pytest.mark.asyncio
async def test_agent_triage_contains_kb_search():
    """Test that triage includes knowledge base search"""
    agent = TriageAgent()
    description = "Checkout error 500 on mobile"
    
    events = []
    async for event_str in agent.triage_stream(description):
        event = json.loads(event_str.strip())
        events.append(event)
    
    # Should have KB search node
    node_starts = [e for e in events if e.get("type") == "node_start"]
    node_names = [e.get("node") for e in node_starts]
    
    assert "search_kb" in node_names


@pytest.mark.asyncio
async def test_agent_triage_classification_structure():
    """Test that classification has required fields"""
    agent = TriageAgent()
    description = "Unable to update billing information"
    
    classification = None
    async for event_str in agent.triage_stream(description):
        event = json.loads(event_str.strip())
        
        if event.get("type") == "classification_complete":
            classification = event.get("data")
            break
    
    # Verify classification structure if not interrupted
    if classification:
        assert "summary" in classification
        assert "category" in classification
        assert "severity" in classification
        assert classification["category"] in ["Billing", "Login", "Performance", "Bug", "Question/How-To"]
        assert classification["severity"] in ["Low", "Medium", "High", "Critical"]


# ============================================================================
# Edge Case Tests
# ============================================================================

def test_triage_with_special_characters():
    """Test triage with special characters in description"""
    payload = {"description": "Error: <script>alert('test')</script> & symbols @#$%"}
    response = client.post("/triage/stream", json=payload)
    
    assert response.status_code == 200


def test_triage_with_unicode():
    """Test triage with unicode characters"""
    payload = {"description": "用户登录失败 - Login failure with Chinese characters 你好"}
    response = client.post("/triage/stream", json=payload)
    
    assert response.status_code == 200


def test_triage_with_line_breaks():
    """Test triage with line breaks in description"""
    payload = {"description": "Issue description:\n\n1. Step one\n2. Step two\n\nError occurred"}
    response = client.post("/triage/stream", json=payload)
    
    assert response.status_code == 200


def test_triage_at_max_length():
    """Test triage with description at exactly max length"""
    payload = {"description": "A" * 5000}  # Exactly MAX_DESCRIPTION_LENGTH
    response = client.post("/triage/stream", json=payload)
    
    assert response.status_code == 200


@pytest.mark.slow
def test_triage_billing_issue(mock_async_openai_client):
    """Test billing issue classification"""
    payload = {"description": "Cannot update my credit card for subscription payment"}
    response = client.post("/triage/stream", json=payload)
    
    assert response.status_code == 200
    
    # Check classification contains billing-related info
    events = []
    for line in response.iter_lines():
        if line:
            events.append(json.loads(line))
    
    classification_events = [e for e in events if e.get("type") == "classification_complete"]
    if classification_events:
        classification = classification_events[0]["data"]
        assert "billing" in classification["summary"].lower() or classification["category"] == "Billing"


# ============================================================================
# Configuration Tests
# ============================================================================

def test_environment_configuration():
    """Test that environment is properly configured"""
    from app.config import get_settings
    
    settings = get_settings()
    assert settings.ENVIRONMENT in ["dev", "prod", "test"]
    assert settings.MAX_RETRIES > 0
    assert settings.PORT > 0
    assert settings.MAX_DESCRIPTION_LENGTH > 0