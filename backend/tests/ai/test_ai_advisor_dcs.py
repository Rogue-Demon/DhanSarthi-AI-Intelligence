"""
Automated Integration & Domain Guard Tests for AI Advisor DCS & Finance-Only Boundary.
"""

import pytest
from app.ai.query_understanding.domain_guard import FinancialDomainGuard
from app.ai.query_understanding.service import QueryUnderstandingService
from app.ai.router import QueryIntent
from app.ai.context.builder import AIContextBuilder
from app.schemas.dashboard import (
    DashboardResponse,
    PeriodInfo,
    UserContextInfo,
    FinancialSummarySnapshot,
    CashFlowSummary,
    NetWorthSummary,
    InvestmentSummary,
    LoanSummary,
    DebtSummary,
    GoalSummary,
    BudgetSummary,
    FinancialHealthSummary,
)
from datetime import date
from decimal import Decimal


@pytest.fixture
def guard():
    return FinancialDomainGuard()


@pytest.fixture
def qu_service():
    return QueryUnderstandingService()


# ---------------------------------------------------------------------------
# Phase 19: 10 Explicit Test Cases for Finance-Only Behavior
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "query,expected_financial",
    [
        # 1. Financial: "What is my credit score?"
        ("What is my credit score?", True),
        # 2. Financial: "Why is my DCS low?"
        ("Why is my DCS low?", True),
        # 3. Financial: "How can I reduce my debt?"
        ("How can I reduce my debt?", True),
        # 4. Financial: "Help me make a monthly budget."
        ("Help me make a monthly budget.", True),
        # 5. Non-Financial Refusal: "Who is the Prime Minister of India?"
        ("Who is the Prime Minister of India?", False),
        # 6. Non-Financial Refusal: "Tell me a joke."
        ("Tell me a joke.", False),
        # 7. Non-Financial Refusal: "Write a Python program."
        ("Write a Python program.", False),
        # 8. Financial: "Can I afford a car?"
        ("Can I afford a car?", True),
        # 9. Non-Financial: "How does a car engine work?"
        ("How does a car engine work?", False),
        # 10. Financial: "Am I ready for a loan?"
        ("Am I ready for a loan?", True),
    ],
)
def test_finance_only_guard_behavior(guard, query, expected_financial):
    res = guard.check_query(query)
    assert res.is_financial is expected_financial, (
        f"Query '{query}' expected is_financial={expected_financial}, got {res.is_financial}"
    )
    if not expected_financial:
        assert res.refusal_message is not None
        assert "DhanSarthi" in res.refusal_message or "financial" in res.refusal_message.lower()


# ---------------------------------------------------------------------------
# Query Understanding Integration Tests for DCS Keywords
# ---------------------------------------------------------------------------

def test_dcs_keywords_classified_as_financial(qu_service):
    for q in [
        "What is my DhanSarthi Creditworthiness Score?",
        "Why did my DCS change?",
        "How to improve my DCS?",
        "Explain loan readiness",
    ]:
        qu = qu_service.analyze(q)
        assert qu.is_financial is True
        assert qu.intent != QueryIntent.OUT_OF_SCOPE


# ---------------------------------------------------------------------------
# System Prompt Assembly & DCS Safety Rules Tests
# ---------------------------------------------------------------------------

def test_system_prompt_includes_dcs_rules():
    builder = AIContextBuilder()
    mock_dashboard = DashboardResponse(
        period=PeriodInfo(start_date=date(2026, 1, 1), end_date=date(2026, 1, 31), period_days=31),
        user=UserContextInfo(user_id=1, display_name="Test", persona="PROFESSIONAL", currency="INR", country="IN"),
        summary=FinancialSummarySnapshot(
            total_income=Decimal("50000"), total_expenses=Decimal("30000"), savings=Decimal("20000"),
            net_worth=Decimal("100000"), total_assets=Decimal("120000"), total_liabilities=Decimal("20000"),
            total_invested=Decimal("50000"), total_debt=Decimal("20000")
        ),
        cash_flow=CashFlowSummary(total_income=Decimal("50000"), total_expenses=Decimal("30000"), net_cash_flow=Decimal("20000"), savings=Decimal("20000"), has_data=True),
        net_worth=NetWorthSummary(total_assets=Decimal("120000"), total_liabilities=Decimal("20000"), net_worth=Decimal("100000"), liquid_assets=Decimal("50000"), has_data=True),
        investments=InvestmentSummary(total_invested=Decimal("50000"), current_value=Decimal("55000"), total_gain_loss=Decimal("5000"), total_return_percentage=Decimal("10"), investment_count=1, has_data=True),
        loans=LoanSummary(total_outstanding=Decimal("20000"), total_principal=Decimal("20000"), total_monthly_emi=Decimal("2000"), loan_count=1, active_loan_count=1, has_data=True),
        debt=DebtSummary(total_debt=Decimal("20000"), monthly_obligations=Decimal("2000"), dti_percent=Decimal("4.0"), has_data=True),
        goals=GoalSummary(total_goals=1, active_count=1, completed_count=0, has_data=True),
        budgets=BudgetSummary(total_budget=Decimal("35000"), total_spending=Decimal("30000"), remaining_budget=Decimal("5000"), overall_utilization_percent=Decimal("85.7"), has_data=True),
        financial_health=FinancialHealthSummary(savings_rate_percent=Decimal("40.0"), dti_percent=Decimal("4.0"), cash_flow_positive=True),
    )

    context = builder.build_context("What is my creditworthiness score?", full_context=mock_dashboard, retrieved_docs=[])
    prompt = builder.build_prompt(context)

    assert "DhanSarthi Creditworthiness Score" in prompt
    assert "NOT a CIBIL score" in prompt
    assert "NEVER calculate a numerical creditworthiness score yourself" in prompt
