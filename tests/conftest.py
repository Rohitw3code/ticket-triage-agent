import pytest
import os
from unittest.mock import AsyncMock, Mock, patch

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["OPENAI_API_KEY"] = "sk-test-key-for-testing"


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing without API calls"""
    with patch("openai.OpenAI") as mock:
        # Mock embeddings
        mock_instance = Mock()
        mock_embeddings = Mock()
        mock_embeddings.create = Mock(return_value=Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        ))
        mock_instance.embeddings = mock_embeddings
        
        # Mock chat completions
        mock_chat = Mock()
        mock_chat.completions = Mock()
        mock_chat.completions.create = Mock(return_value=Mock(
            choices=[Mock(
                message=Mock(
                    content='{"summary": "Test issue", "category": "Bug", "severity": "High", "issue_type": "known_issue", "next_action": "Test action"}'
                )
            )]
        ))
        mock_instance.chat = mock_chat
        
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_async_openai_client():
    """Mock AsyncOpenAI client for async testing"""
    with patch("openai.AsyncOpenAI") as mock:
        mock_instance = Mock()
        
        # Mock embeddings
        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock(return_value=Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        ))
        mock_instance.embeddings = mock_embeddings
        
        # Mock chat completions
        mock_chat = Mock()
        mock_completions = Mock()
        mock_completions.create = AsyncMock(return_value=Mock(
            choices=[Mock(
                message=Mock(
                    content='{"summary": "Test issue", "category": "Bug", "severity": "High", "issue_type": "known_issue", "next_action": "Test action"}'
                )
            )]
        ))
        mock_chat.completions = mock_completions
        mock_instance.chat = mock_chat
        
        mock.return_value = mock_instance
        yield mock


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test"""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["OPENAI_API_KEY"] = "sk-test-key-for-testing"
    yield
