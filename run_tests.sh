#!/bin/bash
# Test runner script for ticket-triage-agent

echo "=================================="
echo "Running Ticket Triage Agent Tests"
echo "=================================="
echo ""

# Set test environment
export ENVIRONMENT=test
export OPENAI_API_KEY=sk-test-key-for-testing

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Running fast tests (excluding slow LLM-dependent tests)..."
echo ""

# Run fast tests only
pytest tests/test_triage.py -v -m "not slow" --tb=short -x

FAST_EXIT_CODE=$?

echo ""
echo "=================================="
echo "Fast Tests Complete"
echo "=================================="
echo ""

if [ $FAST_EXIT_CODE -eq 0 ]; then
    echo "✅ All fast tests passed!"
    echo ""
    echo "To run ALL tests including slow LLM-dependent tests:"
    echo "  pytest tests/test_triage.py -v"
    echo ""
    echo "To run only slow tests:"
    echo "  pytest tests/test_triage.py -v -m slow"
else
    echo "❌ Some tests failed. Exit code: $FAST_EXIT_CODE"
fi

exit $FAST_EXIT_CODE
