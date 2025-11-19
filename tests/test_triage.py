import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


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


def test_triage_valid_ticket():
    """Test triage with valid ticket"""
    response = client.post(
        "/triage",
        json={"description": "Checkout keeps failing with error 500 on mobile"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "category" in data
    assert "severity" in data
    assert "issue_type" in data
    assert "next_action" in data


def test_triage_empty_description():
    """Test triage with empty description"""
    response = client.post(
        "/triage",
        json={"description": ""}
    )
    assert response.status_code == 400


def test_triage_long_description():
    """Test triage with very long description"""
    long_text = "a" * 6000
    response = client.post(
        "/triage",
        json={"description": long_text}
    )
    assert response.status_code == 400


def test_triage_billing_issue():
    """Test billing issue classification"""
    response = client.post(
        "/triage",
        json={"description": "Cannot update my credit card for subscription payment"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category"] in ["Billing", "Bug"]