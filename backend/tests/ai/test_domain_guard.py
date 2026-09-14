"""
Automated Unit & Integration Tests for DhanSarthi Financial Domain Scope Guard.
"""

import pytest
from app.ai.query_understanding.domain_guard import FinancialDomainGuard
from app.ai.query_understanding.service import QueryUnderstandingService
from app.ai.router import QueryIntent


@pytest.fixture
def guard():
    return FinancialDomainGuard()


@pytest.fixture
def qu_service():
    return QueryUnderstandingService()


# ---------------------------------------------------------------------------
# 1. MUST PASS: Financial Questions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "query",
    [
        "How can I reduce my monthly expenses?",
        "Where should I invest ₹10,000 every month?",
        "How much should I save for retirement?",
        "What is an EMI?",
        "Explain compound interest.",
        "How can I reduce my taxes?",
        "Can I afford a ₹50 lakh house?",
        "Should I invest in mutual funds?",
        "How can I improve my financial health?",
        "How should I manage business cash flow?",
        "What is a SIP?",
        "How does an RBI rate hike affect my EMI?",
        "What is my net worth?",
        "Should I buy a house now?",
        "What should I do with my salary?",
        "What is GST?",
        "Calculate EMI for a ₹20 lakh loan.",
        "Analyze my spending.",
    ],
)
def test_financial_queries_must_pass(guard, query):
    res = guard.check_query(query)
    assert res.is_financial is True, f"Query should pass as financial: '{query}'"
    assert res.refusal_message is None


# ---------------------------------------------------------------------------
# 2. MUST REJECT: Non-Financial Questions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "query",
    [
        "Who is India's Prime Minister?",
        "What is the capital of France?",
        "Who won the cricket match?",
        "Tell me a joke.",
        "Write a Python program.",
        "What movie should I watch?",
        "Explain quantum physics.",
        "What is the weather today?",
        "Tell me about Elon Musk.",
    ],
)
def test_non_financial_queries_must_reject(guard, query):
    res = guard.check_query(query)
    assert res.is_financial is False, f"Query should be rejected as non-financial: '{query}'"
    assert res.refusal_message is not None
    assert "DhanSarthi" in res.refusal_message or "financial" in res.refusal_message.lower()
    # Ensure answer is NOT leaked in refusal
    assert "Narendra Modi" not in res.refusal_message
    assert "Paris" not in res.refusal_message


# ---------------------------------------------------------------------------
# 3. Contextual Follow-Up Tests
# ---------------------------------------------------------------------------

def test_contextual_followups(guard):
    class MockMessage:
        def __init__(self, content):
            self.content = content

    # Context 1: Personal income statement
    history1 = [
        MockMessage("I earn ₹60,000 per month."),
        MockMessage("That's a solid monthly income! How can I help you allocate it?"),
    ]
    res1 = guard.check_query("How much should I save?", history=history1)
    assert res1.is_financial is True, "Short query should pass using conversation history context"

    # Context 2: House purchase goal
    history2 = [
        MockMessage("I want to buy a house in 2 years."),
        MockMessage("Great goal! What is your target price?"),
    ]
    res2 = guard.check_query("What loan should I take?", history=history2)
    assert res2.is_financial is True, "Short query should pass using house purchase goal context"


# ---------------------------------------------------------------------------
# 4. Mixed Query Tests
# ---------------------------------------------------------------------------

def test_mixed_query(guard):
    mixed_query = "Who is India's Prime Minister and how might government policy affect my investments?"
    res = guard.check_query(mixed_query)
    assert res.is_financial is True, "Mixed query with financial implications should pass"
    assert res.is_mixed is True


# ---------------------------------------------------------------------------
# 5. Query Understanding Integration Test
# ---------------------------------------------------------------------------

def test_query_understanding_integration(qu_service):
    # Non-financial
    qu1 = qu_service.analyze("Who is India's Prime Minister?")
    assert qu1.is_financial is False
    assert qu1.intent == QueryIntent.OUT_OF_SCOPE
    assert qu1.requires_rag is False
    assert qu1.requires_personal_data is False
    assert qu1.refusal_message is not None

    # Financial
    qu2 = qu_service.analyze("What is the difference between SIP and lumpsum?")
    assert qu2.is_financial is True
    assert qu2.intent != QueryIntent.OUT_OF_SCOPE
    assert qu2.refusal_message is None
